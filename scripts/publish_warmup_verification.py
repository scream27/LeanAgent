"""Publish a complete set of pinned verification artifacts without changing proofs."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

if __package__:
    from .warmup_evaluator import evaluator_metadata
else:
    from warmup_evaluator import evaluator_metadata

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = {'arklib': 'v4.31.0', 'putnambench': 'v4.26.0'}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def errors(result):
    errors = [e['error'] for e in result.get('environments', {}).values() if e.get('error')]
    return errors or ([result['error']] if result.get('error') else [])


def measurement(result):
    if not result['valid']:
        raise ValueError('Cannot publish an invalid measurement')
    env, = result['environments'].values()
    if len(env['runs']) != 4 or env['median_heartbeats'] is None:
        raise ValueError('Expected a check and three fresh measurements')
    return {'tokens': result['tokens'], 'heartbeats': env['median_heartbeats']}


def resource_limited(result):
    return any(e['kind'] == 'timeout' or 'memory_exception' in e.get('message', '')
               for e in errors(result))


def publish(summaries):
    snapshot_path = ROOT / 'dashboard/public/data/warmup-team-results.json'
    manifest_path = ROOT / 'submissions/warmup/manifest.json'
    snapshot = json.loads(snapshot_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    inputs = json.loads((ROOT / 'submissions/warmup/verification-inputs.json').read_text())
    evaluator = evaluator_metadata()
    reports = {}
    for path in summaries:
        report = json.loads(path.read_text())
        if (report['status'] != 'completed' or report['repetitions'] != 3
                or any(report.get(key) != value for key, value in evaluator.items())):
            raise ValueError(f'Incomplete or incompatible verification (expected {evaluator["validatorVersion"]}): {path}')
        key = (report['source'], report['version'], report['revision'])
        if key in reports:
            raise ValueError(f'Duplicate source/version: {key}')
        reports[key] = report
    evidence = {'schemaVersion': 2, **evaluator, 'runs': [], 'problems': []}
    for report in reports.values():
        evidence['runs'].append({k: report[k] for k in [*evaluator, 'source', 'version', 'revision', 'host', 'commit', 'runId', 'manifestSha256', 'dependencies', 'finishedAt']})
    for row in snapshot['problems']:
        if str(row['id']) not in inputs['problems']:
            continue
        meta = inputs['problems'][str(row['id'])]
        pins = [(v, r) for pin in meta['version_info'] for v, r in pin.items()]
        results = {}
        for version, revision in pins:
            report = reports[(row['source'], version, revision)]
            result, = [r for r in report['problems'] if r['id'] == row['id']]
            results[version] = result
        for candidate in row['teamResults']:
            checks, notes = [], []
            source_note = re.split(r'(?:^|\s)v\d+\.\d+\.\d+(?:-[\w.]+)?:|고정 커밋의 의존성을 복원하여', candidate['note'], maxsplit=1)[0].strip()
            if source_note == '지정 환경의 원본과 후보를 재검증했습니다.':
                source_note = ''
            for version, revision in pins:
                result = results[version]
                tested = result['candidates'][candidate['id']]
                if tested['sha256'] != candidate['candidateHash'] or hashlib.sha256(candidate['proof'].encode()).hexdigest() != tested['sha256']:
                    raise ValueError('Candidate changed after verification')
                outcome = tested['result']
                state = 'pending'
                if result['baseline']['valid']:
                    if outcome['valid']:
                        state = 'pass'
                    elif not resource_limited(outcome) and any(e['kind'] in ('compile', 'axioms', 'validation') for e in errors(outcome)):
                        state = 'fail'
                    if not outcome['valid']:
                        reason = '후보 실행 자원 한도' if resource_limited(outcome) else '후보 검증 실패'
                        notes.append(f'{version}: {reason} ' + json.dumps(errors(outcome), ensure_ascii=False)[:600])
                else:
                    notes.append(f'{version}: 고정 환경의 원본 검증 실패 ' + json.dumps(errors(result['baseline']), ensure_ascii=False)[:600])
                checks.append({'version': version, 'revision': revision, 'status': state})
            primary = PRIMARY[row['source']]
            original = results[primary]['baseline']
            tested = results[primary]['candidates'][candidate['id']]['result']
            if any(c['status'] == 'fail' for c in checks):
                status = 'proof_failed'
            elif original['valid'] and tested['valid']:
                status = 'measured' if all(c['status'] == 'pass' for c in checks) else 'partial'
            elif any(c['status'] == 'pass' for c in checks):
                status = 'pending'
            else:
                status = 'blocked'
            candidate.update(status=status, versions=checks, baseline=None, candidate=None,
                             environment=f'{primary} · Linux x86_64 · scaled heartbeat · 독립 프로세스 3회 중앙값 · lean-source-anchored-v1',
                             note=' '.join(filter(None, [source_note, ' '.join(notes) or '고정 커밋의 의존성을 복원하여 원본·후보를 모든 지정 버전에서 재검증했습니다.']))[:2000])
            if status in ('measured', 'partial'):
                candidate['baseline'] = measurement(original)
                candidate['candidate'] = measurement(tested)
        selected, = [c for c in row['teamResults'] if c['id'] == row['selectedCandidateId']]
        for field in ['status', 'versions', 'baseline', 'candidate', 'environment', 'note', 'candidateHash']:
            row[field] = deepcopy(selected[field])
        row['baselineCompatibility'] = 100 if all(r['baseline']['valid'] for r in results.values()) else None
        row['evidence'] = ['submissions/warmup/verification-results.json', f'submissions/warmup/best/P{row["id"]:02}.lean']
        evidence['problems'].append({'id': row['id'], 'versions': results})
        submitted, = [p for p in manifest['problems'] if p['id'] == row['id']]
        if submitted['sha256'] != row['candidateHash']:
            raise ValueError('Submission manifest differs from verified candidate')
        best = ROOT / f'submissions/warmup/best/P{row["id"]:02}.lean'
        if hashlib.sha256(best.read_bytes()).hexdigest() != row['candidateHash']:
            raise ValueError('Best proof changed after verification')
        submitted.update(status=row['status'], versions=deepcopy(row['versions']),
                         allDesignatedVersionsVerified=all(v['status'] == 'pass' for v in row['versions']))
    snapshot['measuredAt'] = max(r['finishedAt'] for r in reports.values())
    verified_problems = '·'.join(f'P{p["id"]:02}' for p in evidence['problems'])
    snapshot['provenance'] = ('PR3 평가기 ' + evaluator['evaluatorRevision']
                              + ' · validator ' + evaluator['validatorVersion']
                              + ' · SHA-256 ' + evaluator['validatorSha256']
                              + '의 원본·후보 동일 환경 3회 중앙값. '
                              + verified_problems + '는 GitHub Actions Linux x86_64에서 지정 커밋 의존성을 복원해 재검증. '
                              '나머지 문제는 기존 로컬 측정 유지. Track1 API 실행 결과 아님.')
    manifest['measuredAt'] = snapshot['measuredAt']
    manifest['dashboardSnapshotSha256'] = hashlib.sha256(encoded(snapshot)).hexdigest()
    manifest['allDesignatedVersionsVerified'] = all(p['allDesignatedVersionsVerified'] for p in manifest['problems'])
    # Validate every candidate and pin before touching any published file.
    snapshot_path.write_bytes(encoded(snapshot))
    manifest_path.write_bytes(encoded(manifest))
    (ROOT / 'submissions/warmup/verification-results.json').write_bytes(encoded(evidence))
    print({p['id']: p['status'] for p in snapshot['problems'] if str(p['id']) in inputs['problems']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('summaries', nargs='+', type=Path)
    publish(parser.parse_args().summaries)
