#!/usr/bin/env python3
"""Stream length-selected proof candidates without Lean or heartbeat execution."""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path

from compare_all_sources import ROOT, SOURCES, inventory_path, read_rows
from compare_tactics import sha256

OUT = ROOT / 'results/warmup_candidates'
SETS = ('ge200', 'top5pct')


def cutoff_top5(hist):
    """Length of the ceil(N/20)-th longest proof; retain every boundary tie."""
    n = sum(hist.values())
    k = (n + 19) // 20
    if not n:
        return None, k, 0
    count = 0
    for length, frequency in sorted(hist.items(), reverse=True):
        count += frequency
        if count >= k:
            return length, k, count
    raise AssertionError('Invalid histogram')


def membership(row, cutoff):
    if row['proof_style'] != 'by' or row['contains_sorry']:
        return []
    length = row['proof_length']
    return ([SETS[0]] if length >= 200 else []) + ([SETS[1]] if cutoff is not None and length >= cutoff else [])


def review_key(row):
    # This is a length-only browsing priority, not predicted contest inclusion.
    return (not row['both_sets'], row['nearest_warmup_log_distance'], -row['proof_length'], row['id'])


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert __import__('shutil').disk_usage(OUT).free > 2 * 1024**3
    length_path = ROOT / 'results/proof_lengths/summary.json'
    lengths = json.loads(length_path.read_text())
    snapshot = json.loads((ROOT / 'data/arena_snapshot.json').read_text())
    warmup_path = ROOT / 'data/arena' / snapshot['arena_revision'] / 'benchmark_data_warmup.jsonl'
    warmups = list(read_rows(warmup_path))
    all_warmup_lengths = [r['proof_length'] for r in warmups]
    sources, input_hashes = {}, {str(length_path.relative_to(ROOT)):sha256(length_path), str(warmup_path.relative_to(ROOT)):sha256(warmup_path)}
    for source in SOURCES:
        folder = OUT / source
        folder.mkdir(exist_ok=True)
        path = inventory_path(ROOT, source)
        digest = sha256(path)
        assert digest == lengths['inputs'][str(path.relative_to(ROOT))], f'Stale length input: {source}'
        input_hashes[str(path.relative_to(ROOT))] = digest
        hist = {int(k):v for k,v in lengths['sources'][source]['subsets']['by_no_direct_sorry']['histogram'].items()}
        cutoff, nominal_k, expected_top = cutoff_top5(hist)
        refs = [(i,r) for i,r in enumerate(warmups,1) if r['source']==source]
        reference_lengths = [r['proof_length'] for _,r in refs] or all_warmup_lengths
        ref_identity = {(r.get('file_path'),r['name']):(i,r) for i,r in refs}
        seen_hist, matched_warmup, counts, metadata = Counter(), [], Counter(), []
        handles = {name:gzip.open(folder / f'{name}.jsonl.gz', 'wt', encoding='utf-8', compresslevel=3) for name in SETS}
        try:
            for inventory_line, row in enumerate(read_rows(path),1):
                if row['proof_style']=='by' and not row['contains_sorry']:
                    seen_hist[row['proof_length']] += 1
                selected = membership(row, cutoff)
                if not selected:
                    continue
                assert hashlib.sha256(row['proof'].encode()).hexdigest()==row['proof_sha256']
                warmup = ref_identity.get((row['file_path'],row['name']))
                warmup_number = warmup[0] if warmup and warmup[1]['proof_length']==row['proof_length'] else None
                if warmup_number:
                    matched_warmup.append(warmup_number)
                length = row['proof_length']
                nearest = min(reference_lengths, key=lambda value:(abs(math.log(length/value)),value))
                selection = {'sets':selected, 'both_sets':len(selected)==2, 'top5pct_cutoff':cutoff,
                             'eligible_source_population':sum(hist.values()), 'warmup_number':warmup_number,
                             'nearest_warmup_length':nearest, 'nearest_warmup_log_distance':abs(math.log(length/nearest)),
                             'warmup_length_basis':'same_source' if refs else 'all_15_no_source_specific_warmup',
                             'within_warmup_length_range':min(reference_lengths)<=length<=max(reference_lengths)}
                exported = {**row, 'candidate_selection':selection, 'original_corpus_root':source,
                            'original_inventory':str(path.relative_to(ROOT)), 'original_inventory_line':inventory_line,
                            'context_path_from_repository_root':str(Path(source)/row['context_file'])}
                line = json.dumps(exported, ensure_ascii=False)+'\n'
                for name in selected:
                    handles[name].write(line)
                    counts[name] += 1
                counts['union'] += 1
                counts['intersection'] += len(selected)==2
                metadata.append({k:row[k] for k in ['id','source','name','file_path','declaration_line','proof_length','num_lines','proof_sha256','context_file','source_link']} | selection)
        finally:
            for handle in handles.values():
                handle.close()
        assert seen_hist==hist, source
        assert counts['ge200']==sum(n for length,n in hist.items() if length>=200)
        assert counts['top5pct']==expected_top
        assert counts['union']==counts['ge200']+counts['top5pct']-counts['intersection']
        assert len({r['id'] for r in metadata})==len(metadata)
        metadata.sort(key=review_key)
        for name in SETS:
            with (folder/f'{name}.index.jsonl').open('w') as stream:
                for row in metadata:
                    if name in row['sets']:
                        stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        with (folder/'intersection.index.jsonl').open('w') as stream:
            for row in metadata:
                if row['both_sets']:
                    stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        preview = [r for r in metadata if r['warmup_number'] is None][:25]
        with (folder/'review_first.jsonl').open('w') as stream:
            for row in preview:
                stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        stat = {'eligible':sum(hist.values()), 'ge200':counts['ge200'], 'top5pct':counts['top5pct'],
                'top5pct_cutoff':cutoff, 'nominal_top5_count':nominal_k, 'boundary_tie_extra':counts['top5pct']-nominal_k,
                'selected_top_percent':round(100*counts['top5pct']/sum(hist.values()),4) if hist else None,
                'intersection':counts['intersection'], 'union':counts['union'], 'warmup_numbers':sorted(matched_warmup),
                'preview_non_warmup':len(preview), 'warmup_length_basis':'same_source' if refs else 'all_15_no_source_specific_warmup'}
        lines = [f'# {source}: warm-up 길이 후보', '',
                 f"모집단 {stat['eligible']:,}개. 200토큰 이상 {stat['ge200']:,}개, 상위 5% {stat['top5pct']:,}개, 교집합 {stat['intersection']:,}개.", '',
                 f"상위 5% 경계: {cutoff if cutoff is not None else '대상 없음'} 토큰. 경계 동률을 모두 포함한다. 기존 warm-up도 전체 목록에는 포함하고 번호로 표시한다.", '',
                 '- [200토큰 이상 전체 증명](ge200.jsonl.gz) · [탐색용 인덱스](ge200.index.jsonl)',
                 '- [상위 5% 전체 증명](top5pct.jsonl.gz) · [탐색용 인덱스](top5pct.index.jsonl)',
                 '- [교집합 인덱스](intersection.index.jsonl) · [먼저 볼 후보 25개 이하](review_first.jsonl)', '',
                 '## 먼저 볼 후보', '',
                 '기존 warm-up을 제외하고 두 조건을 모두 만족하는 후보를 먼저, 그 안에서는 warm-up 길이와의 로그 비율 차이가 작은 순서다. 같은 출처의 warm-up 길이를 사용하며 LeanPool만 전체 15개의 길이를 참고한다. 수학적 내용·tactic·heartbeat 유사도나 출제 확률 순위가 아니다.', '',
                 '| ID | 정리 | 토큰 | 선택 조건 | 가까운 warm-up 길이 | 원문 |', '| --- | --- | ---: | --- | ---: | --- |']
        for row in preview:
            context = ROOT/source/row['context_file']
            assert context.exists(), context
            rel = os.path.relpath(context,folder)
            name = row['name'].replace('|','\\|')
            lines.append(f"| {row['id']} | `{name}` | {row['proof_length']:,} | {'둘 다' if row['both_sets'] else '200 이상' if 'ge200' in row['sets'] else '상위 5%'} | {row['nearest_warmup_length']:,} | [파일](<{rel}>) · {row['declaration_line']}행 |")
        if not preview:
            lines.append('대상 없음. PutnamBench 원본은 직접 sorry를 포함하므로, 완성된 warm-up 3개는 별도 참조 자료로 사용한다.')
        lines += ['', '원문 문맥·버전·검증 상태는 전체 증명 레코드에 유지된다. `context_file`은 `original_corpus_root` 기준 상대경로이며 `context_path_from_repository_root`는 저장소 루트 기준 경로다. 독립 컴파일 가능한 문제 파일이라고 가정하지 않는다.', '']
        (folder/'README.md').write_text('\n'.join(lines))
        stat['exports'] = {p.name:sha256(p) for p in folder.iterdir() if p.is_file() and p.name!='manifest.json'}
        write_json(folder/'manifest.json',stat)
        sources[source] = stat
        print(source, json.dumps({k:stat[k] for k in ['ge200','top5pct','top5pct_cutoff','intersection']}),flush=True)
    assert sorted(i for s in sources.values() for i in s['warmup_numbers'])==list(range(1,13))
    summary = {'scope':'proof_style=by AND contains_sorry=false; same population as proof_lengths main distribution',
               'metric':'warm-up-calibrated Arena proof_length, including leading by',
               'top5_rule':'K=ceil(N/20); choose length >= length of K-th longest proof, keeping all ties; no selection if N=0',
               'index_order':'intersection first, nearest same-source warm-up length by absolute log ratio, length descending, ID; LeanPool uses all 15 warm-up lengths',
               'full_record_order':'original inventory order; use index JSONL for browsing priority',
               'sources':sources, 'inputs':input_hashes, 'script_sha256':sha256(Path(__file__)),
               'heartbeat_measured':False, 'lean_executed':False, 'original_corpora_modified':False}
    write_json(OUT/'summary.json',summary)
    lines = ['# Warm-up과 비슷한 길이의 후보', '',
             '직접 `sorry/admit`가 없는 `:= by` 증명에서 두 조건을 독립적으로 추렸다. Arena 토큰 수는 시작의 `by`를 포함하며 warm-up 공개 길이 15/15를 재현하는 기존 계산값을 사용한다. Heartbeat 측정과 Lean 실행은 하지 않았다.', '',
             '| 출처 | 모집단 | 200토큰 이상 | 상위 5% 경계 | 상위 5% | 두 조건 교집합 |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for source,s in sources.items():
        lines.append(f"| [{source}]({source}/README.md) | {s['eligible']:,} | {s['ge200']:,} | {s['top5pct_cutoff'] if s['top5pct_cutoff'] is not None else '—'} | {s['top5pct']:,} | {s['intersection']:,} |")
    lines += ['', '## 상위 5% 경계', '',
              '출처별 모집단 N에서 길이 내림차순 ceil(N/20)번째 정리의 길이를 경계로 잡고, 그 길이의 모든 동률을 포함한다. 따라서 정확히 5%보다 조금 많을 수 있다. 이전 분포 보고서의 선형 보간 P95 숫자와는 정의가 다르다. LeanPool은 경계 동률로 명목 개수보다 '+str(sources['leanpool']['boundary_tie_extra'])+'개 더 포함한다.', '',
              '## 읽는 순서', '',
              '각 출처 README에 기존 warm-up을 제외한 미리보기 25개 이하를 제공한다. 교집합을 먼저 보고, 그 안에서는 같은 출처의 warm-up 길이에 가까운 순서로 정렬했다. LeanPool은 자체 warm-up이 없어 전체 15개의 길이를 참고한다. 길이만으로 정한 탐색 순서이며 예상 출제 목록이나 의미적 유사도 순위가 아니다.', '',
              '- `ge200.jsonl.gz`와 `top5pct.jsonl.gz`: 서로 독립적인 전체 증명 레코드. 명제·증명·문맥 위치·해시·버전 정보를 유지한다.',
              '- `*.index.jsonl`: 위 탐색 순서로 정렬한 가벼운 메타데이터. 전체 증명 파일은 원본 inventory 순서다.',
              '- `intersection.index.jsonl`: 두 조건을 모두 만족하는 후보. 같은 길이 척도의 하한 필터이므로 교집합은 더 엄격한 쪽 목록과 같다.',
              '- 원본에 있는 warm-up 1–12번은 두 목록 모두에서 확인했고 `warmup_number`로 표시했다. PutnamBench 원본은 대상이 없으며 [완성된 warm-up 3개](../all_sources/putnambench_warmup_references.jsonl)는 원본 문제집에 섞지 않았다.',
              '- 직접 sorry 제외는 커널·공리 검증 완료를 의미하지 않는다. 버전 간 동일 선언 여부도 이번에는 새로 검사하지 않았다. 필터 밖 원본 정리는 그대로 보존했다.', '',
              '재생성: `python3 scripts/select_warmup_candidates.py` (저장소 루트에서 실행). 단일 Python 프로세스로 스트리밍하며 원본 정리 파일을 수정하지 않는다.', '']
    (OUT/'README.md').write_text('\n'.join(lines))


if __name__=='__main__':
    main()
