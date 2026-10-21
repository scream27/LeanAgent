#!/usr/bin/env python3
"""Bounded, source-only comparison of six extracted declaration inventories."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from compare_tactics import Aggregate, category, extended_heads, sha256
from survey import mask_noncode

from arena_workspace import ROOT
SOURCES = ('strata', 'physlib', 'cslib', 'arklib', 'putnambench', 'leanpool')


def read_rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def inventory_path(root, source):
    for name in ('inventory.jsonl.gz', 'inventory.jsonl'):
        path = root / source / name
        if path.exists():
            return path
    raise FileNotFoundError(f'{source}: no completed inventory')


def collect(path, output):
    aggregates = {name: Aggregate() for name in ('all', 'no_direct_sorry', 'by_style')}
    extraction_methods = Counter()
    path_groups = Counter()
    seen = set()
    for row in read_rows(path):
        if row['id'] in seen:
            raise ValueError(f'Duplicate ID in {path}: {row["id"]}')
        seen.add(row['id'])
        proof = row['proof']
        if hashlib.sha256(proof.encode()).hexdigest() != row['proof_sha256']:
            raise ValueError(f'Proof hash mismatch: {row["id"]}')
        hits = extended_heads(proof)
        aggregates['all'].add(row, hits)
        if not row['contains_sorry']:
            aggregates['no_direct_sorry'].add(row, hits)
        if row['proof_style'] == 'by':
            aggregates['by_style'].add(row, hits)
        method = row.get('extraction_method', 'native_lean_ast')
        extraction_methods[method] += 1
        parts = row['file_path'].split('/')
        if row['source'] == 'leanpool' and len(parts) > 1 and parts[0] == 'LeanPool':
            path_groups[parts[1]] += 1
        counts = Counter(h['tactic'] for h in hits)
        output.write(json.dumps({
            'source': row['source'], 'id': row['id'], 'name': row['name'],
            'file_path': row['file_path'], 'proof_sha256': row['proof_sha256'],
            'contains_sorry': row['contains_sorry'], 'extraction_method': method,
            'heads': dict(counts),
            'simp_forms': dict(Counter(h['form'] for h in hits if 'form' in h)),
        }, ensure_ascii=False) + '\n')
    return {'subsets': {k: v.summary() for k, v in aggregates.items()},
            'extraction_methods': dict(extraction_methods),
            'leanpool_path_group_declarations': dict(path_groups.most_common())}


def warmup_references(root, out):
    snapshot = json.loads((root / 'data/arena_snapshot.json').read_text())
    path = root / 'data/arena' / snapshot['arena_revision'] / 'benchmark_data_warmup.jsonl'
    refs = []
    for number, row in enumerate(read_rows(path), 1):
        if row['source'] != 'putnambench':
            continue
        position = row['src'].find(row['statement'])
        if position < 0:
            raise ValueError('Warm-up statement not found')
        end = position + len(row['statement'])
        rest = row['src'][end:]
        if not rest.lstrip().startswith(':='):
            raise ValueError('Unsupported standalone warm-up proof delimiter')
        proof = rest[rest.index(':=') + 2:]
        import re
        refs.append({**row, 'id': f'arena_warmup_{number:02}',
                     'source': 'putnambench_warmup', 'proof': proof,
                     'proof_sha256': hashlib.sha256(proof.encode()).hexdigest(),
                     'proof_style': 'by' if proof.lstrip().startswith('by') else 'term',
                     'declaration_kind': 'theorem',
                     'contains_sorry': bool(re.search(r'\b(?:sorry|admit|sorryAx)\b', mask_noncode(proof))),
                     'extraction_method': 'arena_standalone_reference',
                     'environment_hashes_are': 'mathlib4_commits_not_putnambench_commits'})
    target = out / 'putnambench_warmup_references.jsonl'
    target.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in refs))
    return target, {str(path.relative_to(root)): sha256(path)}


def render(data):
    lines = ['# 여섯 출처의 추출·tactic 비교', '',
             '모든 통계는 추출한 증명 문자열에 동일한 확장 어휘 집계기를 적용한 근사치다. Lean 빌드·커널 검사·heartbeat 측정은 실행하지 않았다.', '',
             'PutnamBench 원본의 미완성 문제와 Arena의 완성된 warm-up 참조 증명은 별도로 집계한다. LeanPool은 여러 하위 프로젝트를 포함한 큰 코퍼스이며 단순 합산 점유율로 다른 출처를 평가하지 않는다.', '',
             '| 출처 | 조사 Lean 파일 | 추출 정리 | 직접 sorry 제외 | 미분리 선언 |',
             '| --- | ---: | ---: | ---: | ---: |']
    for source in SOURCES:
        s = data['sources'][source]
        m = s['manifest']
        lines.append(f"| {source} | {m.get('files_scanned', '—'):,} | {s['subsets']['all']['declarations']:,} | {s['subsets']['no_direct_sorry']['declarations']:,} | {m.get('unresolved_declarations', 0):,} |")
    lines += ['', '## 출처별 많이 등장한 tactic', '',
              '직접 `sorry`가 없는 추출 정리만 사용한다. 이는 공리 검증 완료라는 뜻이 아니다. 각 항목은 **등장 횟수 / 사용 정리 수 (해당 분모 대비 비율)**다. term 겸용 표기·분기·conv·wrapper는 이 상위 표에서 제외했다.', '',
              '| 출처 | 분모 | 상위 tactic 5개 |', '| --- | ---: | --- |']
    for source, s in data['sources'].items():
        a = s['subsets']['no_direct_sorry']
        top = [h for h in a['heads'] if category(h['name']) == 'tactic_candidate'][:5]
        text = '; '.join(f"`{h['name']}` {h['occurrences']:,} / {h['declarations']:,} ({h['prevalence_percent']:.1f}%)" for h in top) or '집계 가능한 완성 증명 없음'
        lines.append(f"| {source} | {a['declarations']:,} | {text} |")
    lines += ['', '## 같은 tactic의 사용 정리 비율', '',
              '분모는 각 출처의 직접 sorry 제외 추출 정리다. 감지된 tactic이 없는 정리도 분모에 포함한다. 0%는 현재 집계기가 감지하지 않았다는 의미다.', '',
              '| tactic | ' + ' | '.join(SOURCES) + ' |',
              '| --- | ' + ' | '.join('---:' for _ in SOURCES) + ' |']
    for tactic in ('simp', 'rw', 'simp_all', 'grind', 'exact', 'apply', 'intro', 'intros', 'induction', 'cases', 'ext', 'ring', 'norm_num', 'omega', 'fun_prop', 'aesop'):
        cells = []
        for source in SOURCES:
            a = data['sources'][source]['subsets']['no_direct_sorry']
            h = next((h for h in a['heads'] if h['name'] == tactic), {})
            cells.append(f"{h.get('prevalence_percent', 0):.1f}%" if a['declarations'] else '—')
        lines.append(f"| `{tactic}` | " + ' | '.join(cells) + ' |')
    groups = data['sources']['leanpool']['leanpool_path_group_declarations']
    total = data['sources']['leanpool']['subsets']['all']['declarations']
    lines += ['', '## LeanPool 내부 분포', '',
              '`LeanPool/<경로 그룹>/`별 추출 정리 수 상위 10개다. 증명의 의미적 중복을 제거한 수가 아니다.', '',
              '| 경로 그룹 | 추출 정리 | LeanPool 추출 정리 대비 |', '| --- | ---: | ---: |']
    for group, count in list(groups.items())[:10]:
        lines.append(f'| {group} | {count:,} | {100 * count / total:.1f}% |')
    lines += ['', '## 기준 환경과 한계', '']
    for source in SOURCES:
        m = data['sources'][source]['manifest']
        lines.append(f"- **{source}**: `{m.get('revision')}`, `{m.get('toolchain')}`. 추출 방식: `{data['sources'][source]['extraction_methods']}`.")
    lines += ['',
              '- CSLib·ArkLib은 Arena warm-up 공통 소스 커밋이다. PutnamBench·LeanPool은 2026-10-14 수집 시 HEAD를 고정했다. PutnamBench warm-up의 version_info 커밋은 Mathlib 환경이며 원본 문제집의 커밋이 아니다.',
              '- 새 네 출처는 lexical/layout 추출이다. 네이티브 AST나 컴파일 검증이 아니며, 미분리 항목은 각 코퍼스 ledger에 남긴다. 파싱 실패 파일 수 등은 각 manifest를 확인한다.',
              '- 추출기의 기존 네이티브 증명 범위 교차검사 기록은 [native_calibration.json](../remaining_sources/native_calibration.json)에 보존했다. 이는 새 출처 전체의 문법 검증을 대신하지 않는다.',
              '- 이름 있는 theorem/lemma만 대상으로 하므로 def/instance/example와 매크로 생성 정리는 포함하지 않는다. 반복·생성 코드와 복제된 증명이 통계를 키울 수 있으며 의미적으로 중복 제거하지 않았다.',
              '- allowlist 밖 custom tactic, syntax quotation, term/tactic 문맥 구별에는 한계가 있다. `<;>` 뒤 tactic은 소스에 적힌 횟수만 센다. 빈도가 비용을 뜻하지 않는다.',
              '- `summary.json`에는 전체 / 직접 sorry 제외 / by 형태 통계를 모두 담았다. `declarations.jsonl.gz`는 선언별 빈도다. 기존 두 출처 비교 보고서는 그대로 보존했다.', '',
              '```bash', 'source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent-LeanRefactorArena',
              'python3 scripts/compare_all_sources.py', '```', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/all_sources')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    ref_path, inputs = warmup_references(args.root, args.output)
    config = args.root / 'data/remaining_sources.json'
    inputs[str(config.relative_to(args.root))] = sha256(config)
    sources = {}
    with gzip.open(args.output / 'declarations.jsonl.gz', 'wt', encoding='utf-8', compresslevel=3) as output:
        for source in SOURCES:
            path = inventory_path(args.root, source)
            manifest = args.root / source / 'manifest.json'
            inputs[str(path.relative_to(args.root))] = sha256(path)
            inputs[str(manifest.relative_to(args.root))] = sha256(manifest)
            sources[source] = {**collect(path, output), 'manifest': json.loads(manifest.read_text())}
            print(source, sources[source]['subsets']['all']['declarations'], flush=True)
        sources['putnambench_warmup'] = collect(ref_path, output)
    data = {'method': 'same extended lexical counter as scripts/compare_tactics.py; no dynamic execution',
            'heartbeat_measured': False, 'sources': sources, 'inputs': inputs,
            'scripts': {str(path.relative_to(ROOT)): sha256(path) for path in
                        (Path(__file__), ROOT / 'scripts/compare_tactics.py', ROOT / 'scripts/survey.py')}}
    (args.output / 'summary.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (args.output / 'report.md').write_text(render(data))


if __name__ == '__main__':
    main()
