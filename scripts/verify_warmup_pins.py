"""Restore exact library pins and measure warmup proofs with the frozen PR3 evaluator.

Builds run in the supplied work directory. Evidence is written separately; this
command never edits candidates, published scores, or upstream tracked sources.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_REVISION = 'c18ec56682462847e2f4d8b6d60aa79ec071a10b'
REPOSITORIES = {'arklib': 'https://github.com/Verified-zkEVM/ArkLib.git',
                'putnambench': 'https://github.com/leanprover-community/mathlib4.git'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def trailing_doc_start(text):
    """Locate the immediately trailing declaration doc, respecting nested comments.

    Module docs (/-!) are independent commands and must never be measured as the target.
    """
    i=0; last=None
    while i<len(text):
        if text.startswith('--',i):
            end=text.find('\n',i); i=len(text) if end<0 else end
        elif text.startswith('/-',i):
            start=i; depth=1; i+=2
            while i<len(text) and depth:
                if text.startswith('/-',i): depth+=1; i+=2
                elif text.startswith('-/',i): depth-=1; i+=2
                else: i+=1
            if depth: raise ValueError('Unclosed context comment')
            last=(start,i)
        elif text[i]=='"':
            i+=1
            while i<len(text):
                if text[i]=='\\': i+=2
                elif text[i]=='"': i+=1; break
                else: i+=1
        else: i+=1
    if last and not text[last[1]:].strip() and text.startswith('/--',last[0]): return last[0]
    return None

def template(meta, source):
    original = meta['src']
    if source.count(original) == 0:
        # Older ArkLib pins differ by horizontal spacing in this declaration.
        # Match the same text without changing line boundaries or other context.
        pattern = r'[ \t]+'.join(re.escape(part) for part in re.split(r'[ \t]+', original))
        matches = list(re.finditer(pattern, source))
        if len(matches) == 1:
            original = matches[0].group()
    if source.count(original) != 1:
        raise ValueError('공식 원본 선언과 소스 문맥의 일치 위치를 유일하게 찾지 못함')
    prefix, suffix = source.split(original)
    # Move attached documentation and scoped commands WITH the target into the
    # evaluator input, preserving them in both baseline and candidate compilation.
    # Otherwise a doc comment / `set_option ... in` attaches to the instrumentation.
    lead = ''
    start = trailing_doc_start(prefix)
    if start is not None:
        lead, prefix = prefix[start:], prefix[:start]
    while True:
        match = re.search(r'(?m)^(?:set_option [^\n]+ in|omit [^\n]+ in|@\[[^\n]+\])\s*\Z', prefix)
        if not match: break
        lead, prefix = prefix[match.start():] + lead, prefix[:match.start()]
    body = prefix + '{{DECLARATION}}\n' + suffix
    imports = list(re.finditer(r'(?m)^(?:(?:public|private|meta) )*import [^\n]+\n', body))
    if not imports: raise ValueError('No import boundary for the instrumentation')
    boundary = imports[-1].end()
    body = body[:boundary] + '{{HARNESS_COMMANDS}}\n' + body[boundary:]
    module = re.search(r'(?m)^module\s*\n',body)
    pos = module.end() if module else 0
    return body[:pos] + '{{HARNESS_IMPORT}}\n' + body[pos:], lead


def main(args):
    work, output = args.work.resolve(), args.output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=False)
    snapshot = json.loads((ROOT / 'dashboard/public/data/warmup-team-results.json').read_text())
    inputs = json.loads((ROOT / 'submissions/warmup/verification-inputs.json').read_text())
    rows = []
    for row in snapshot['problems']:
        if row['source'] != args.source or str(row['id']) not in inputs['problems']:
            continue
        meta = inputs['problems'][str(row['id'])]
        pins = {v: r for pin in meta['version_info'] for v, r in pin.items()}
        if args.version in pins:
            rows.append((row, meta, pins[args.version]))
    if not rows or len({r for _, _, r in rows}) != 1:
        raise ValueError('Expected one exact source revision for this source/version')
    revision = rows[0][2]
    report = {'source': args.source, 'version': args.version, 'revision': revision,
              'evaluatorRevision': EVALUATOR_REVISION, 'repetitions': 3,
              'startedAt': datetime.now(timezone.utc).isoformat(),
              'host': platform.platform(), 'commit': os.environ.get('GITHUB_SHA'),
              'runId': os.environ.get('GITHUB_RUN_ID'), 'status': 'preparing', 'problems': []}
    write(output / 'summary.json', report)
    counter = 0
    def run(command, cwd=work, capture=False):
        nonlocal counter
        counter += 1
        print('+', ' '.join(map(str, command)), flush=True)
        logfile = output / f'prepare-{counter:02}.log'
        with logfile.open('w') as log:
            result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, text=True)
        text = logfile.read_text()
        print(text[-4000:], flush=True)
        if result.returncode:
            raise RuntimeError(f'{command[0]} failed ({result.returncode}); see {logfile.name}: {text[-2000:]}')
        return text.strip() if capture else None
    try:
        project = work / 'project'
        run(['git', 'init', str(project)])
        run(['git', 'remote', 'add', 'origin', REPOSITORIES[args.source]], project)
        run(['git', 'fetch', '--depth=1', 'origin', revision], project)
        run(['git', 'checkout', '--detach', 'FETCH_HEAD'], project)
        if run(['git', 'rev-parse', 'HEAD'], project, True) != revision:
            raise ValueError('Source revision mismatch')
        toolchain = (project / 'lean-toolchain').read_text().strip()
        if toolchain != f'leanprover/lean4:{args.version}':
            raise ValueError(f'Toolchain mismatch: {toolchain}')
        lock = (project / 'lake-manifest.json').read_bytes()
        run(['elan', 'toolchain', 'install', toolchain], project)
        run(['lake', 'exe', 'cache', 'get'], project)
        target = '+ArkLib.ProofSystem.Binius.BinaryBasefold.Prelude:olean' if args.source == 'arklib' else '+Mathlib:olean'
        if (project / 'lake-manifest.json').read_bytes() != lock:
            raise ValueError('Preparation changed the pinned dependency manifest')
        packages = []
        for package in json.loads(lock)['packages']:
            if package['type'] != 'git':
                raise ValueError('Unexpected non-git dependency in pinned manifest')
            # Old Lake manifests serialize escaped Lean names with guillemets,
            # but the package directory uses the unescaped identifier.
            name = package['name']
            directory = name[1:-1] if name.startswith('«') and name.endswith('»') else name
            path = project / '.lake/packages' / directory
            head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
            if head != package['rev']:
                raise ValueError(f'Dependency revision mismatch: {package["name"]}')
            packages.append({'name': package['name'], 'revision': head})
        report['dependencies'] = packages
        report['manifestSha256'] = sha(lock)
        run(['lake', 'build', target], project)
        if (project / 'lake-manifest.json').read_bytes() != lock:
            raise ValueError('Build changed the pinned dependency manifest')
        if sys.platform == 'linux':
            run(['free', '-m'])
        if args.source == 'putnambench':
            probe = output / 'import-probe.lean'
            probe.write_text('import Mathlib\nimport Aesop\n#check Nat\n')
            run(['lake', 'env', 'lean', f'-M{args.memory_mb}', str(probe)], project)
        runtime = work / 'evaluator'
        names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', EVALUATOR_REVISION, 'refactor_eval'], text=True).splitlines()
        for name in names:
            dest = runtime / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{EVALUATOR_REVISION}:{name}']))
        sys.path.insert(0, str(runtime))
        from refactor_eval.lean import LeanEvaluator
        from refactor_eval.tokens import TOKENIZER_ID
        evaluator = LeanEvaluator()
        report['tokenizer'] = TOKENIZER_ID
        for row, meta, _ in rows:
            ident = f'P{row["id"]:02}'
            source = (project / meta['file_path']).read_text() if meta['file_path'] else meta['header'] + meta['src']
            context, lead = template(meta, source)
            env = {'id': args.version.replace('.', '-'), 'project': str(project),
                   'toolchain': toolchain, 'command': ['lake', 'env', 'lean', '-j1', f'-M{args.memory_mb}', '-T200000'],
                   'template': context, 'timeout_seconds': 180}
            evidence = output / ident
            evidence.mkdir()
            (evidence / 'context.lean.in').write_text(context)
            config = {'statement': lead + meta['statement'], 'name': meta['name']}
            result = {'id': row['id'], 'sourceSha256': sha(source.encode()),
                      'fingerprint': evaluator.fingerprint(env), 'candidates': {}}
            report['problems'].append(result)
            baseline = evaluator.evaluate(lead + meta['src'], config, [env], evidence / 'baseline', 3)
            if args.memory_mb < 8192 and any('memory_exception' in e.get('error', {}).get('message', '')
                    for e in baseline.get('environments', {}).values() if e.get('error')):
                write(evidence / f'baseline-result-{args.memory_mb}MiB.json', baseline)
                env['command'] = ['lake', 'env', 'lean', '-j1', '-M8192', '-T200000']
                result['fingerprint'] = evaluator.fingerprint(env)
                result['resourceRetry'] = {'initialMemoryMiB': args.memory_mb, 'finalMemoryMiB': 8192}
                baseline = evaluator.evaluate(lead + meta['src'], config, [env], evidence / 'baseline-8192MiB', 3)
            result['baseline'] = baseline
            write(evidence / 'baseline-result.json', baseline)
            seen = {}
            for candidate in row['teamResults']:
                code = candidate['proof']
                digest = sha(code.encode())
                if digest != candidate['candidateHash']:
                    raise ValueError('Published candidate hash mismatch')
                if candidate['id'] == row['selectedCandidateId']:
                    if (ROOT / f'submissions/warmup/best/{ident}.lean').read_bytes() != code.encode():
                        raise ValueError('Selected best file differs from published candidate')
                if not baseline['valid']:
                    measured = {'valid': False, 'error': {'kind': 'baseline', 'message': 'Original failed in the pinned environment'}}
                elif digest in seen:
                    measured = seen[digest]
                else:
                    measured = evaluator.evaluate(lead + code, config, [env], evidence / digest[:16], 3)
                    seen[digest] = measured
                result['candidates'][candidate['id']] = {'sha256': digest, 'result': measured}
            write(evidence / 'result.json', result)
            write(output / 'summary.json', report)
            print(ident, 'baseline:', baseline['valid'], 'candidates:', {k: v['result']['valid'] for k, v in result['candidates'].items()}, flush=True)
        report['status'] = 'completed'
    except Exception as error:
        report['status'] = 'environment_failed'
        report['error'] = str(error)
        (output / 'error.log').write_text(traceback.format_exc())
        raise
    finally:
        report['finishedAt'] = datetime.now(timezone.utc).isoformat()
        write(output / 'summary.json', report)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            lines = [f'### {args.source} {args.version}',
                     'Workflow completion records an attempt; proof validity is shown below.',
                     '', '| Problem | Original | Candidate | Valid |', '|---|---|---|---|']
            for item in report['problems']:
                for name, candidate in item['candidates'].items():
                    lines.append(f'| P{item["id"]:02} | {item["baseline"]["valid"]} | {name} | {candidate["result"]["valid"]} |')
            if report.get('error'):
                lines.extend(['', 'Preparation failed. See the error.log artifact.'])
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary_file:
                summary_file.write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=REPOSITORIES, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--memory-mb', type=int, default=6144)
    main(parser.parse_args())
