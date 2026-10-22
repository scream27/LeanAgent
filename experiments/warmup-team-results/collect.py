"""Import a pinned, explicitly selected set of team artifacts; never choose by score."""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent
BENCHMARK = '56aa7b8f738d1d6a0a24a55e03cdea1a84007b6c'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class PreBlocks(HTMLParser):
    def __init__(self):
        super().__init__(); self.blocks = []; self.inside = False
    def handle_starttag(self, tag, attrs):
        if tag == 'pre': self.inside = True; self.blocks.append('')
    def handle_endtag(self, tag):
        if tag == 'pre': self.inside = False
    def handle_data(self, value):
        if self.inside: self.blocks[-1] += value


def collect(leanagent):
    commit = subprocess.check_output(['git', '-C', str(leanagent), 'rev-parse', 'HEAD'], text=True).strip()
    prefix = Path('docs/research/refactoring/warmup')
    benchmark = ROOT / 'benchmarks/arena' / BENCHMARK / 'benchmark_data_warmup.jsonl'
    problems = [json.loads(line) for line in benchmark.read_text().splitlines()]
    manifest = {'schemaVersion': 1, 'sourceRepository': 'https://github.com/Pseudo-Lab/LeanAgent',
                'sourceCommit': commit, 'benchmarkRevision': BENCHMARK,
                'benchmarkSha256': digest(benchmark.read_bytes()), 'problems': []}
    owners = ['남성우','남성우','권주원','정소미','박성호','권주원','손지연','박선영','정소미','박성호','박선영','손지연','권주원','박채원','박채원']
    for number, meta in enumerate(problems, 1):
        row = {'id': number, 'name': meta['name'], 'source': meta['source'], 'assignedAuthor': owners[number-1],
               'representativeId': None, 'selectionReason': '', 'candidates': []}
        base = EXP / 'configs' / f'P{number:02}'
        save(base / 'problem.json', meta)
        (base / 'baseline.lean').write_text(meta['src'] + '\n')
        (base / 'statement.lean').write_text(meta['statement'])
        manifest['problems'].append(row)

        def add(author, relative, kind='declaration', block=None, suffix='final', note=''):
            src = leanagent / prefix / relative
            raw = src.read_bytes(); text = raw.decode()
            source_path = (prefix / relative).as_posix()
            committed = subprocess.run(['git','-C',str(leanagent),'show',f'{commit}:{source_path}'],capture_output=True)
            source_state = 'committed' if committed.returncode == 0 and committed.stdout == raw else 'working-tree-snapshot'
            extract = {'kind': kind, 'blocks': block}
            if kind == 'html-body':
                parser = PreBlocks(); parser.feed(text)
                # The author's HTML contains separate statement and tactic-body blocks.
                statement_index, body_index = block
                code = parser.blocks[statement_index].rstrip() + ' := by\n' + parser.blocks[body_index].rstrip() + '\n'
            elif kind == 'markdown':
                blocks = re.findall(r'```lean\n(.*?)```', text, re.S)
                code = '\n'.join(blocks[i] for i in block)
            elif kind == 'body':
                code = meta['statement'] + ' := ' + text.rstrip() + '\n'
            else:
                code = text
            # File-level imports/options are retained as source, but NOT injected into the pinned context.
            # Only strip an explicit preamble when the exact official statement occurs once.
            preamble = ''
            if code.count(meta['statement']) == 1 and not code.startswith(meta['statement']):
                idx = code.index(meta['statement'])
                if not re.search(r'(?m)^(?:private )?(?:lemma|theorem|def)\b', code[:idx]):
                    preamble, code = code[:idx], code[idx:]
            cid = f'{author}-{suffix}'
            folder = EXP / 'candidates' / f'P{number:02}' / cid
            folder.mkdir(parents=True, exist_ok=True)
            (folder / ('source' + src.suffix)).write_bytes(raw)
            (folder / 'candidate.lean').write_text(code)
            if preamble: (folder / 'preamble.lean.txt').write_text(preamble)
            entry = {'id': cid, 'author': author, 'path': str((folder/'candidate.lean').relative_to(ROOT)),
                     'sha256': digest(code.encode()), 'sourcePath': source_path, 'sourceCommit': commit,
                     'sourceSha256': digest(raw), 'sourceState': source_state, 'extraction': extract, 'preamble': preamble,
                     'note': note, 'generation': 'historical-team-experiment; not a Track1 API run'}
            row['candidates'].append(entry)
            save(folder/'provenance.json',entry)
            return cid

        if number in (1,2): add('남성우','남성우/report.html','html-body', [0,2] if number==1 else [3,5])
        if number in (4,9): add('정소미',f'정소미/evidence/P{number}/final.lean')
        if number in (5,10): add('박성호',f'박성호/evidence/P{number:02}.lean')
        if number==7: add('손지연','손지연/report.md','markdown',[2])
        if number==12: add('손지연','손지연/report.md','markdown',[5,6], note='보조정리 전체를 보존. 단일 선언만 받는 PR3 평가기에서는 지원 범위 확인 필요.')
        if number in (14,15): add('박채원','박채원/report.md','markdown',[1 if number==14 else 3])
        hist = f'권주원/evidence/2026-10-16-warmup15-xhigh/P{number:02}'
        best = json.loads((leanagent/prefix/hist/'best.json').read_text())
        if best.get('best'):
            if digest((leanagent/prefix/hist/'best.lean').read_bytes()) != best['best']['proof_sha256']:
                raise ValueError(f'Historical selected proof hash mismatch: P{number:02}')
            add('권주원',hist+'/best.lean','body',suffix='20261016',note='기존 best.json에 선택된 후보. 이번 수집에서 점수로 재선택하지 않음.')
        elif number==13:
            add('권주원',hist+'/development-best.lean','body',suffix='development',note='추가 import를 사용한 개발 후보. 지정 환경에서 별도 재검증 필요.')
        if row['candidates']:
            row['representativeId'] = row['candidates'][0]['id']
            row['selectionReason'] = '담당자가 공유한 최종본 우선. 없으면 명시적으로 선택된 팀 실험 후보를 표시. 점수 순위 선정 아님.'
        else:
            row['selectionReason'] = '공유된 개선 후보 없음. 원본 fallback은 팀원 후보로 등록하지 않음.'
    save(EXP/'manifest.json', manifest)
    print('Imported',sum(len(p['candidates']) for p in manifest['problems']),'candidates across',len(problems),'problems')

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--leanagent',type=Path,required=True)
    collect(parser.parse_args().leanagent.resolve())
