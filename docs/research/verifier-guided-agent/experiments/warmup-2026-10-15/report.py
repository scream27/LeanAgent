"""Aggregate observed versions, select strict improvements, emit offline policy prompts."""
import csv
from collections import Counter
import json
import re
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import escalation_policy as policy
ROWS=[json.loads(l) for l in (HERE/'reference/benchmark_data_warmup.jsonl').read_text().splitlines()]
CANDS=[json.loads(l) for l in (HERE/'candidates.jsonl').read_text().splitlines()]
REF={r['name']:r['heartbeat'] for r in map(json.loads,(HERE/'reference/benchmark_heartbeats.jsonl').read_text().splitlines())}


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def diagnostic_text(path):
    if not path:
        return []
    # Preserve original absolute command paths as provenance; allow the text
    # artifact bundle to be moved or cloned on another machine.
    portable=HERE/'runs'/path.split('/runs/',1)[1] if '/runs/' in path else Path(path)
    return portable.read_text()


def main():
    table=[]; selected=[]
    for n,row in enumerate(ROWS,1):
        versions=[v for p in row['version_info'] for v in p]
        primary=versions[0]
        runs={}
        for v in versions:
            path=HERE/'runs'/f'{n:02d}'/v/'results.json'
            if path.exists(): runs[v]=json.loads(path.read_text())
        base={v:r.get('baseline',{}) for v,r in runs.items()}
        primary_base=base.get(primary,{})
        complete_base=all(base.get(v,{}).get('kind')=='valid' for v in versions)
        baseline_score=100/3 if complete_base else None
        best={'score':baseline_score,'body':None,'label':'original'}
        for c in [c for c in CANDS if c['problem_id']==n]:
            observations={}
            locals={}
            for v,r in runs.items():
                entry=next((z for z in r.get('candidates',[]) if z['prompt_id']==c['prompt_id']),{})
                observations[v]=entry.get('observation',{})
                locals[v]=entry.get('local',{})
            pool=[{'body':c['proof_body'],'origin':'raw','observations':observations}]
            search_only=[]
            for derived in locals.get(primary,{}).get('derived',[]):
                body=derived['proof_body']
                # `?` is a discovery operator, not a submission candidate.
                # Preserve its validation logs but score the extracted proof.
                if derived.get('search_query_only') or (derived['origin']=='local_repair' and re.search(r'\b(?:simp|simp_all|aesop|exact)\?',body)):
                    search_only.append(derived['origin'])
                    continue
                obs={}
                for v in versions:
                    d=next((d for d in locals.get(v,{}).get('derived',[]) if d['proof_body']==body),{})
                    obs[v]=d.get('observation',{})
                pool.append({'body':body,'origin':derived['origin'],'observations':obs})
            for item in pool:
                obs=item['observations']; first=obs.get(primary,{})
                complete=all(obs.get(v,{}).get('kind') in {'valid','invalid','invalid_axioms','contract_reject'} for v in versions)
                # Preserve the baseline axiom budget, not just a global allowlist.
                axioms_ok=all(o.get('kind')!='valid' or set(o.get('axioms') or [])<=set(base.get(v,{}).get('axioms') or []) for v,o in obs.items())
                score=None
                if (complete_base and complete and axioms_ok and first.get('kind')=='valid'
                    and first.get('heartbeats') is not None and primary_base.get('heartbeats',0)>0
                    and primary_base.get('tokens',0)>0):
                    robust=100*sum(obs[v]['kind']=='valid' for v in versions)/len(versions)
                    score=(100*(1-first['tokens']/primary_base['tokens'])+100*(1-first['heartbeats']/primary_base['heartbeats'])+robust)/3
                item.update(score=score,coverage_complete=complete,axioms_ok=axioms_ok)
                if score is not None and (best['score'] is None or score>best['score']):
                    best={'score':score,'body':item['body'],'label':c['prompt_id']+'/'+item['origin']}
            eligible=[p for p in pool if p['score'] is not None]
            chosen=max(eligible,key=lambda p:p['score']) if eligible else pool[0]
            first=chosen['observations'].get(primary,{})
            raw=pool[0]
            if c['user_excluded']:
                outcome='unchanged_user_excluded'
            elif raw['body']==c['original_body']:
                outcome='unchanged'
            elif raw['score'] is not None:
                outcome='improved' if raw['score']>baseline_score else 'worse' if raw['score']<baseline_score else 'tied'
            elif observations.get(primary,{}).get('kind') in {'invalid','invalid_axioms','contract_reject'}:
                outcome='invalid'
            else:
                outcome='blocked_or_incomplete'
            any_valid_unscored=any(p['score'] is None and p['observations'].get(primary,{}).get('kind')=='valid' for p in pool)
            final=('improved' if chosen['score'] is not None and chosen['score']>baseline_score else
                   'original_fallback' if complete_base and (outcome in {'unchanged','unchanged_user_excluded'} or
                       (not any_valid_unscored and (chosen['coverage_complete'] or outcome=='invalid'))) else 'unresolved')
            entry={'problem_id':n,'name':row['name'],'prompt':c['prompt_id'],'raw_outcome':outcome,
                   'search_only_candidates':len(search_only),
                   'valid_pool_members_unscored':sum(p['score'] is None and p['observations'].get(primary,{}).get('kind')=='valid' for p in pool),
                   'raw_score':raw['score'],'best_local_score':chosen['score'],'chosen_origin':chosen['origin'],
                   'baseline_score':baseline_score,'final_outcome':final,'checked_versions':len(runs),'listed_versions':len(versions),
                   'official_length':row['proof_length'],'local_baseline_tokens':primary_base.get('tokens'),
                   'official_heartbeat':REF[row['name']],'local_baseline_heartbeat':primary_base.get('heartbeats'),
                   'candidate_tokens':first.get('tokens'),'candidate_heartbeat':first.get('heartbeats')}
            table.append(entry)
            # Policy preview: never invent an API price for a prompt-only experiment.
            folder=HERE/'policy'/f'{n:02d}'/c['prompt_id']
            baseline_path=HERE/'runs'/f'{n:02d}'/primary/'baseline.lean'
            if baseline_path.exists():
                source=baseline_path.read_text().removesuffix('\n#print axioms '+row['name']+'\n')
                if source.count(row['src'])!=1: continue
                start=source.index(row['src'])+len(row['src'])-len(c['original_body'])
                end=start+len(c['original_body'])
                body=chosen['body']; ph=policy.digest(body)
                eh=policy.digest(json.dumps({'versions':row['version_info'],'source_hash':runs.get(primary,{}).get('source_hash')},sort_keys=True))
                loc=locals.get(primary,{})
                state='valid' if first.get('kind')=='valid' else 'invalid' if first.get('kind') in {'invalid','invalid_axioms','contract_reject'} else 'environment_error'
                diagpath=first.get('output_path')
                req={'problem_id':row['name'],'status':state,'baseline_verified':primary_base.get('kind')=='valid',
                     'preview_only':True,'environment':row['version_info'],'environment_hash':eh,
                     'statement':row['statement'],'context':source[:start], 'original_proof':c['original_body'],
                     'candidate_proof':body,'candidate_hash':ph,
                     'source_contract':{'original_source':source,'candidate_source':source[:start]+body+source[end:],
                                        'body_start':start,'body_end':end},
                     'diagnostics':diagnostic_text(diagpath),
                     'localization':{'scope':'body'},
                     'local':{'state':loc.get('state','pending'),'evidence':loc.get('attempts') or [loc.get('reason','No completed local pass')]},
                     'llm_history':[], 'incumbent':{'score':baseline_score,'proof_body':c['original_body']},
                     'constraints':['Preserve exact statement and context','No sorry/new axioms/declarations','No target theorem self-reference'],
                     'metrics':{}}
                if chosen['score'] is not None:
                    req['metrics']={'baseline_tokens':primary_base['tokens'],'baseline_heartbeats':primary_base['heartbeats'],
                        'candidate_tokens':first['tokens'],'candidate_heartbeats':first['heartbeats'],
                        'versions_passed':sum(o.get('kind')=='valid' for o in chosen['observations'].values()),
                        'versions_total':len(versions),'incumbent_score':baseline_score,'all_versions_checked':True,
                        'candidate_hash':ph,'environment_hash':eh,'comparable_to_incumbent':True}
                decision=policy.decide(req) if not c['user_excluded'] else {'action':'USER_EXCLUDED','prompt':None,'api_called':False}
                save(folder/'request.json',req); save(folder/'decision.json',decision)
                if decision.get('prompt'): (folder/'prompt.txt').write_text(decision['prompt'])
                elif (folder/'prompt.txt').exists(): (folder/'prompt.txt').unlink()
                entry['policy_action']=decision['action']
        selected.append({'problem_id':n,'name':row['name'],'selection':best['label'], 'score':best['score'],
                         'proof_body':best['body'] or next(c['original_body'] for c in CANDS if c['problem_id']==n),
                         'baseline_complete':complete_base})
    save(HERE/'results.json',table); save(HERE/'selected.json',selected)
    keys=list(dict.fromkeys(k for row in table for k in row))
    with (HERE/'results.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(table)
    fmt=lambda x: '—' if x is None else f'{x:.4f}'
    lines=['# Warm-up 모의 실행 결과','',
           '점수는 공식 제출 점수가 아닌 로컬 모의 점수입니다. 원본의 모든 지정 버전 통과 점수는 33.3333입니다.',
           'P1: 구조 유지 간소화 · P2: 구조 개선 · P3: 비용 축소. 모델에 escalation 요청을 보내지 않았습니다.', '',
           '| 문제 | 선택 | 원본 점수 | 선택 점수 | 판정 |',
           '|---|---|---:|---:|---|']
    for s in selected:
        items=[t for t in table if t['problem_id']==s['problem_id']]
        unresolved=any(t['final_outcome']=='unresolved' or t['valid_pool_members_unscored'] for t in items)
        verdict=('판정 보류' if unresolved or not s['baseline_complete'] else
                 '성공(개선)' if s['selection']!='original' else '원본 보존(사용자 지정)' if s['problem_id']==8 else '아무것도 못함(원본 fallback)')
        lines.append(f"| {s['problem_id']} | {s['selection']} | {fmt(items[0]['baseline_score'])} | {fmt(s['score'])} | {verdict} |")
    lines += ['', '| 프롬프트 | 최초 개선 | 최초 악화 | 최초 invalid | 원본 유지 | 미완료 | 처리 후 개선 |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for prompt in ['P1','P2','P3']:
        group=[t for t in table if t['prompt']==prompt]
        counts=Counter(t['raw_outcome'] for t in group)
        lines.append(f"| {prompt} | {counts['improved']} | {counts['worse']} | {counts['invalid']} | {counts['unchanged']+counts['unchanged_user_excluded']} | {counts['blocked_or_incomplete']} | {sum(t['final_outcome']=='improved' for t in group)} |")
    lines += ['', '단순 프롬프트 결과와 로컬 수리·최적화 이후 결과를 아래에서 구분합니다. invalid는 컴파일 실패이며, worse는 검증은 통과했지만 점수가 낮아진 경우입니다.', '',
           'o200k_base token counts; synchronous Lean declaration heartbeats. Not official Arena scores.',
           'Rows with missing environments/versions are unresolved, never silently treated as proof failures.',
           'Candidates were frozen before feedback; model escalation prompts are printed only.', '',
           '| ID | Prompt | Raw outcome | Raw score | Best local score | Final | Policy |',
           '|---|---|---|---:|---:|---|---|']
    for t in table:
        lines.append(f"| {t['problem_id']} | {t['prompt']} | {t['raw_outcome']} | {fmt(t['raw_score'])} | {fmt(t['best_local_score'])} | {t['final_outcome']} | {t.get('policy_action','—')} |")
    lines += ['', '공개 기준값과 로컬 원본 계측의 비교입니다. 공식 길이를 로컬 점수의 분모로 혼합하지 않습니다.', '',
              '| 문제 | 공개 길이 | 로컬 토큰 | 공개 heartbeat | 로컬 heartbeat |',
              '|---|---:|---:|---:|---:|']
    for t in table[::3]:
        lines.append(f"| {t['problem_id']} | {t['official_length']} | {t['local_baseline_tokens']} | {t['official_heartbeat']} | {fmt(t['local_baseline_heartbeat'])} |")
    emitted=sorted((HERE/'policy').glob('*/*/prompt.txt'))
    lines += ['', f'출력한 escalation 프롬프트: {len(emitted)}개. 실제 모델 호출: 0회.', '']
    for path in emitted:
        lines.append(f'- [{path.parent.parent.name}번 / {path.parent.name}]({path.relative_to(HERE).as_posix()})')
    lines += ['', '재현 방법·계측 범위·검증기 한계는 [README](README.md), 실제 선택 proof body는 [selected.json](selected.json), 전체 수치는 [results.csv](results.csv)에 있습니다.',
              '실제 escalation 프롬프트는 policy/문제번호/프롬프트이름/prompt.txt에 저장합니다. 호출 권한과 예산 승인을 뜻하지 않는 preview입니다.',
              '이 실험은 같은 대화 문맥에서 생성한 단일 후보 실험이므로 프롬프트의 일반적인 우열을 입증하지 않습니다. 1·2번은 사전 노출이 있습니다.']
    if all(t['final_outcome']!='unresolved' and not t['valid_pool_members_unscored'] for t in table):
        improved=sum(s['selection']!='original' for s in selected)
        lines += ['', f"최종 선택: {improved}문제 개선, {len(selected)-improved}문제 원본 유지. 선택 점수 평균은 {sum(s['score'] for s in selected)/len(selected):.4f}입니다. 검증 누락 여부는 [audit.json](audit.json)을 확인하세요."]
    lines += ['', '관찰에서 얻은 설계상 결론:', '',
              '- 5번: 같은 문제에서 P1 개선, P2 악화, P3 컴파일 실패가 자연스럽게 발생했다. 검증 통과와 점수 개선을 구분해야 한다.',
              '- 9번 P1: 첫 오류 줄의 `exact?` 탐색에서 명시적 `exact ChoiceBisim.choice h`를 추출했다. 같은 수정 body가 세 버전을 통과했지만 원본보다 점수가 낮아 fallback했다. “수리 성공”은 “선택 성공”이 아니다.',
              '- 13번: `simp?`의 제안을 명시적으로 추출한 후보가 최초 후보보다 높은 점수를 얻었다. LLM 없이도 유효한 최적화 후보를 만들 수 있었다.',
              '- 15번 P3: 유효하지만 점수가 낮은 후보를 버리고 원본을 유지하는 분기가 실제로 실행됐다. 최종 문제별 선택에서는 더 나은 다른 프롬프트의 후보를 사용한다.',
              '- 이 결과만으로 신뢰 가능한 tactic-state localization, 악의적인 문맥 변경 방어, 모델을 호출한 뒤의 재수리 루프까지 검증했다고 주장하지 않는다. 해당 기능은 이번 실험의 범위 밖이며 escalation은 body 단위 프롬프트 출력에서 끝냈다.']
    (HERE/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print('Reported',len(table),'rows;',sum(s['baseline_complete'] for s in selected),'complete baseline version sets')


if __name__=='__main__':main()
