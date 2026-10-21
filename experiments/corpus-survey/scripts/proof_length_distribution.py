#!/usr/bin/env python3
"""Stream the six corpora and compare warm-up-calibrated Arena proof lengths."""
from __future__ import annotations

import ast
from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re

from compare_all_sources import ROOT, SOURCES, inventory_path, read_rows
from compare_tactics import sha256
from proof_tokens import proof_length

OUT = ROOT / 'results/proof_lengths'
EDGES = [0, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, math.inf]
LABELS = ['0–9', '10–24', '25–49', '50–99', '100–249', '250–499', '500–999', '1,000–2,499', '2,500–4,999', '5,000–9,999', '10,000+']
SUBSETS = ['by_no_direct_sorry', 'by_all', 'term_no_direct_sorry', 'assignment_no_direct_sorry', 'assignment_all']
DISPLAY = {'strata':'Strata', 'physlib':'PhysLib', 'cslib':'CSLib', 'arklib':'ArkLib', 'putnambench':'PutnamBench', 'leanpool':'LeanPool', 'warmup':'Warm-up'}
COLORS = dict(zip(SOURCES, ['#31588c', '#14958b', '#996b24', '#865aa7', '#db6842', '#596779']))


def quantile(hist, q):
    n = sum(hist.values())
    if not n:
        return None
    position = (n - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    cumulative = 0
    a = b = None
    for value, count in sorted(hist.items()):
        if cumulative <= lo < cumulative + count:
            a = value
        if cumulative <= hi < cumulative + count:
            b = value
            break
        cumulative += count
    return round(a + (b - a) * (position - lo), 4)


def describe(hist):
    n = sum(hist.values())
    bins = [sum(c for v, c in hist.items() if left <= v < right) for left, right in zip(EDGES, EDGES[1:])]
    assert sum(bins) == n
    return {'n':n, 'min':min(hist) if n else None, 'max':max(hist) if n else None,
            'mean':round(sum(v*c for v,c in hist.items()) / n, 4) if n else None,
            **{f'p{p}':quantile(hist, p/100) for p in [10,25,50,75,90,95,99]},
            'bin_counts':bins, 'bin_percent':[round(100*c/n, 4) for c in bins] if n else [None]*len(bins),
            'histogram':dict(sorted(hist.items()))}


def public_calibration(warmup):
    path = ROOT / 'data/proof_length_reference/utils.py'
    names = {'proof_length', 'remove_comments', 'extract_and_remove_attributes', '_parse_single_attribute', 'return_theorem_to_prove_mathlib_style'}
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    # Pure reviewed functions only. Compatibility for Python 3.9; strict=False
    # is the sole strict argument used by the public function.
    def compat_zip(*args, strict=False):
        assert strict is False
        return zip(*args)
    namespace = {'re':re, 'zip':compat_zip}
    module = ast.Module(body=ast.parse('from __future__ import annotations').body + nodes, type_ignores=[])
    exec(compile(module, str(path), 'exec'), namespace)
    result = []
    for i, row in enumerate(warmup, 1):
        calibrated = proof_length(row['src'], row['statement'])
        assert calibrated == row['proof_length'], i
        result.append({'number':i, 'source':row['source'], 'name':row['name'], 'published':row['proof_length'],
                       'known_boundary_counter':calibrated, 'current_public_function':namespace['proof_length'](row['src'])})
    return {'rows':result, 'known_boundary_matches':15, 'current_public_matches':sum(r['published']==r['current_public_function'] for r in result),
            'reference_sha256':sha256(path), 'difference_reason':'Warm-up 11: public signature scanner stops at let P_i := inside the proposition; known statement boundary reproduces published 1906 instead of 2219.'}


def collect():
    OUT.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads((ROOT/'data/arena_snapshot.json').read_text())
    warmup_path = ROOT/'data/arena'/snapshot['arena_revision']/'benchmark_data_warmup.jsonl'
    warmup = list(read_rows(warmup_path))
    calibration = public_calibration(warmup)
    sources, inputs = {}, {str(warmup_path.relative_to(ROOT)):sha256(warmup_path)}
    with gzip.open(OUT/'lengths.jsonl.gz', 'wt', compresslevel=3) as output:
        for source in SOURCES:
            path = inventory_path(ROOT, source)
            inputs[str(path.relative_to(ROOT))] = sha256(path)
            counters = {s:Counter() for s in SUBSETS}
            scope = Counter()
            for row in read_rows(path):
                scope['all_extracted'] += 1
                style = row['proof_style']
                scope['style_'+style] += 1
                if style not in ('by', 'term'):
                    scope['non_assignment_excluded'] += 1
                    continue
                length = proof_length(row['src'], row['statement'])
                assert length == row['proof_length'], (source, row['id'], length, row['proof_length'])
                assert hashlib.sha256(row['proof'].encode()).hexdigest() == row['proof_sha256']
                counters['assignment_all'][length] += 1
                if style == 'by':
                    counters['by_all'][length] += 1
                    scope['by_direct_sorry'] += bool(row['contains_sorry'])
                if not row['contains_sorry']:
                    counters['assignment_no_direct_sorry'][length] += 1
                    counters['by_no_direct_sorry' if style=='by' else 'term_no_direct_sorry'][length] += 1
                output.write(json.dumps({'source':source, 'id':row['id'], 'name':row['name'],
                                        'proof_length':length, 'proof_style':style, 'contains_sorry':row['contains_sorry'],
                                        'proof_sha256':row['proof_sha256']}, ensure_ascii=False)+'\n')
            sources[source] = {'scope':dict(scope), 'subsets':{s:describe(h) for s,h in counters.items()}}
            print(source, sources[source]['subsets']['by_no_direct_sorry']['n'], flush=True)
    warmup_rows = []
    for i, row in enumerate(warmup, 1):
        length = row['proof_length']
        hist = sources[row['source']]['subsets']['by_no_direct_sorry']['histogram']
        n = sum(hist.values())
        warmup_rows.append({'number':i, 'source':row['source'], 'name':row['name'], 'proof_length':length,
                            'source_percentile_le':round(100*sum(c for v,c in hist.items() if v<=length)/n, 4) if n else None})
    summary = {'metric':'Arena Appendix J lexer, known extracted statement boundary, calibrated to all 15 published warm-up lengths; includes leading by',
               'primary_subset':'by_no_direct_sorry', 'percentile_method':'linear interpolation, rank (n-1)*q',
               'bins':{'lower_bounds':EDGES[:-1], 'upper_bounds':EDGES[1:-1]+[None], 'labels':LABELS},
               'sources':sources, 'warmup':describe(Counter(r['proof_length'] for r in warmup)),
               'warmup_rows':warmup_rows, 'warmup_by_source':{s:describe(Counter(r['proof_length'] for r in warmup if r['source']==s)) for s in SOURCES},
               'calibration':calibration, 'inputs':inputs,
               'scripts':{str(p.relative_to(ROOT)):sha256(p) for p in [Path(__file__), ROOT/'scripts/proof_tokens.py']},
               'heartbeat_measured':False}
    (OUT/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    return summary


def render(data):
    def fmt(v):
        return '—' if v is None else f'{v:,.1f}'.removesuffix('.0')
    rows = [(DISPLAY[s],data['sources'][s]['subsets']['by_no_direct_sorry']) for s in SOURCES] + [('Warm-up 15',data['warmup'])]
    lines = ['# Arena 기준 증명 길이 분포', '',
             '주 분포: 추출한 `:= by` 형태 정리 중 직접 `sorry/admit`가 없는 증명. 단위는 Arena 토큰 수이며 `:=`는 제외하고 시작의 `by`는 포함한다. 줄 수·문자 수·LLM 토큰 수와 다르다. 주석은 제외한다.', '',
             'Arena warm-up 공개 길이 **15/15 일치**를 기준으로 사용했다. 명제·선언부는 이미 추출한 정확한 경계로 제외한다. 새 증명의 값은 로컬 재현값이며 Arena 서버 재평가 값은 아니다.', '',
             '![길이 분포](distribution.png)', '',
             '| 출처 | 대상 수 | 중앙값 | 평균 | P90 | P99 | 최대 |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for label, stat in rows:
        lines.append('| '+label+' | '+' | '.join(fmt(stat[k]) for k in ['n','p50','mean','p90','p99','max'])+' |')
    lines += ['', 'P90은 90%의 증명이 그 길이 이하인 지점을 선형 보간한 값이다. 출처별 비율로 비교하며, 규모가 큰 LeanPool을 합산해 다른 출처의 분포를 덮지 않는다.', '',
              '## Warm-up 15개', '', '![Warm-up 길이](warmup_lengths.png)', '',
              '| 번호 | 출처 | 정리 | 토큰 수 | 해당 출처 내 누적 백분위 |', '| ---: | --- | --- | ---: | ---: |']
    for row in data['warmup_rows']:
        lines.append(f"| {row['number']} | {DISPLAY[row['source']]} | `{row['name']}` | {row['proof_length']:,} | {fmt(row['source_percentile_le'])}{'%' if row['source_percentile_le'] is not None else ''} |")
    lines += ['', '백분위는 같은 출처의 주 분포에서 warm-up 길이 이하인 증명의 비율이다. PutnamBench는 완성 증명 분모가 없어 비교하지 않는다. Warm-up은 선택된 예제 15개로, 무작위 표본이나 본 대회 전체 분포가 아니다.', '',
              '## 포함·제외 범위', '', '| 출처 | 전체 정리 | by 전체 | by 직접 sorry | 주 분포 | term 직접 sorry 제외 | 방정식·구조체 등 |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for source in SOURCES:
        s=data['sources'][source];scope=s['scope'];sub=s['subsets']
        lines.append(f"| {DISPLAY[source]} | {scope['all_extracted']:,} | {sub['by_all']['n']:,} | {scope.get('by_direct_sorry',0):,} | {sub['by_no_direct_sorry']['n']:,} | {sub['term_no_direct_sorry']['n']:,} | {scope.get('non_assignment_excluded',0):,} |")
    lines += ['',
              '- `summary.json`에는 주 분포 외에 sorry 포함 by 전체, term, 대입형 전체 분포도 별도로 제공한다. `lengths.jsonl.gz`는 대입형 정리별 길이와 proof SHA다. 원본 코퍼스는 수정하지 않았다.',
              '- PutnamBench 원본 672개는 모두 sorry를 포함한다. 원본의 빈 분포를 길이 0으로 표시하지 않는다. warm-up PutnamBench 3개는 별도의 완성된 참조 증명이다.',
              '- 직접 sorry 제외는 커널·공리 검증 완료를 뜻하지 않는다. 중복 증명을 제거하지 않았으며, 길이가 heartbeat 비용을 뜻하지 않는다.',
              '- 출처마다 Lean 버전과 추출 방식이 다르다. 기준 커밋과 파싱 한계는 [여섯 출처 비교](../all_sources/report.md)를 참조한다.', '',
              '## 계산 기준 검증', '',
              '[저자 공개 proof_length 코드](https://github.com/delta-lab-ai/lean-refactor/blob/main/lean_refactor/utils.py)의 lexer와 같은 토큰화 규칙을 사용한다. 공개 함수 전체를 그대로 적용하면 14/15만 일치한다. Warm-up 11번 명제 내부 `let P_i :=`를 증명 시작으로 잡아 2,219를 반환하지만, 공개 benchmark 값은 1,906이다. 정확한 statement 경계를 사용하는 기존 `scripts/proof_tokens.py`는 15/15를 재현한다. 두 결과를 summary의 calibration에 모두 보존했다.', '',
              '재계산한 모든 대입형 길이와 기존 inventory의 proof_length가 일치함을 검사했다. 공개 코드 스냅샷·해시는 `data/proof_length_reference/`에 저장했다. 순위 통계와 빈 구간 처리는 단위 테스트로 검사했다.', '',
              '```bash', 'source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent-LeanRefactorArena',
              '/Users/jwkweon/00_work/00_project/env/05_pseudolab/LeanAgent-LeanRefactorArena/.venv/bin/python scripts/proof_length_distribution.py', '```', '']
    (OUT/'report.md').write_text('\n'.join(lines))


def plot(data):
    os.environ.setdefault('MPLCONFIGDIR', str(Path(os.environ['PROJECT_CACHE_DIR'])/'matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    import numpy as np
    font = Path('/System/Library/Fonts/Supplemental/AppleGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False, 'font.size':11, 'savefig.facecolor':'white'})
    stats=[data['sources'][s]['subsets']['by_no_direct_sorry'] for s in SOURCES]+[data['warmup']]
    labels=[DISPLAY[s] for s in SOURCES]+['Warm-up']
    matrix=np.array([[v if v is not None else np.nan for v in s['bin_percent']] for s in stats])
    fig, ax=plt.subplots(figsize=(14,6.5))
    cmap=plt.get_cmap('Blues').copy();cmap.set_bad('#eeeeee')
    im=ax.imshow(matrix,aspect='auto',cmap=cmap,vmin=0,vmax=max(np.nanmax(matrix),1))
    ax.set_yticks(range(7),[f'{label}  (n={s["n"]:,})' for label,s in zip(labels,stats)])
    ax.set_xticks(range(len(LABELS)),LABELS,fontsize=9)
    ax.set_xlabel('증명 길이 · Arena 토큰 수',labelpad=12)
    for i,s in enumerate(stats):
        for j,p in enumerate(s['bin_percent']):
            ax.text(j,i,'—' if p is None else f'{p:.1f}%',ha='center',va='center',fontsize=10,
                    color='white' if p is not None and p>np.nanmax(matrix)*.58 else '#203247')
    fig.suptitle('출처별 증명 길이 분포',fontsize=21,x=.02,ha='left',y=.99)
    ax.set_title('직접 sorry가 없는 := by 증명 · 행별 비율 합계 100% · 시작의 by 포함',loc='left',fontsize=12,pad=15)
    fig.colorbar(im,ax=ax,pad=.018,label='해당 출처의 증명 비율 (%)',shrink=.85)
    ax.tick_params(length=0);[sp.set_visible(False) for sp in ax.spines.values()]
    fig.text(.02,.015,'PutnamBench 원본은 대상 0개. Warm-up의 PutnamBench 참조 증명 3개는 마지막 행에 포함. 소수점 반올림 적용.',fontsize=10,color='#526174')
    fig.tight_layout(rect=[0,.06,1,.92])
    fig.savefig(OUT/'distribution.png',dpi=160);fig.savefig(OUT/'distribution.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,8))
    rows=data['warmup_rows'];values=[r['proof_length'] for r in rows]
    ax.barh(range(15),values,color=[COLORS[r['source']] for r in rows],height=.65)
    ax.set_yticks(range(15),[f"{r['number']:02d}  {DISPLAY[r['source']]}" for r in rows]);ax.invert_yaxis()
    for i,v in enumerate(values):ax.text(v+45,i,f'{v:,}',va='center',fontsize=11)
    ax.set_xlim(0,max(values)*1.14);ax.set_xlabel('Arena 공개 proof_length · 토큰 수')
    ax.set_title('Warm-up 15개 증명 길이',fontsize=21,loc='left',pad=22)
    ax.xaxis.grid(True,color='#e4e9ee');ax.set_axisbelow(True)
    for side in ['top','right','left']:ax.spines[side].set_visible(False)
    ax.tick_params(axis='y',length=0)
    fig.text(.02,.015,'공개 길이 15/15 재현 · 중앙값 '+f"{data['warmup']['p50']:,.0f}"+' 토큰 · 정리별 전체 이름은 보고서에 수록',fontsize=10,color='#526174')
    fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(OUT/'warmup_lengths.png',dpi=160);fig.savefig(OUT/'warmup_lengths.svg');plt.close(fig)


if __name__ == '__main__':
    result=collect()
    render(result)
    plot(result)
