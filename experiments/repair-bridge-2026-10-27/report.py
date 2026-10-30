"""Generate readable report and explicit common-harness/Arena JSON exports."""
import collections, html, json, re
from pathlib import Path
from bridge import HERE,REPO,harness
from diagnostics import diagnostics,bounded_feedback
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
from lean_agent.evaluator.tokens import proof_body

def score(m,b):return (100*(1-m['tokens']/b['tokens'])+100*(1-m['raw_heartbeats']/b['raw_heartbeats'])+100)/3

def cost(m,b):return .5*(m['tokens']/b['tokens']+m['raw_heartbeats']/b['raw_heartbeats'])
def generate():
 report={'schema_version':1,'date':'2026-10-27','official_evaluation':False,'api_calls':0,'provenance':harness.read(HERE/'provenance.json'),'score_note':'Common cost lower is better. For these one-version problems, local final score = 100 - 200/3 * common cost. Fresh 3-sample raw heartbeat median.','problems':[]}
 followup_path=REPO/'runs/repair-bridge-2026-10-27/1/json-query-followup/summary.json'
 followup=harness.read(followup_path) if followup_path.exists() else None
 if followup:
  assert not any(x.get('beats_selected') for x in followup['results']), 'Integrate improved follow-up before exporting'
  report['json_query_followup']=followup
 report['escalation_requests']=[]
 for n in (1,2):
  d=REPO/'runs/repair-bridge-2026-10-27'/str(n)/'escalation/001'
  if (d/'decision.json').exists():
   decision=harness.read(d/'decision.json');target=HERE/'escalation'/f'p{n}.prompt.txt';target.parent.mkdir(exist_ok=True)
   target.write_text((d/'prompt.txt').read_text())
   report['escalation_requests'].append({'problem_id':n,'action':decision['action'],'scope':decision['scope'],'api_called':False,'prompt_file':str(target.relative_to(HERE))})
 cards=[];table=[];exports=[]
 for n in (1,2):
  root=REPO/'runs/repair-bridge-2026-10-27'/str(n);raw=root/'raw'
  problem=harness.read(raw/'input/problem.json');summary=harness.read(raw/'summary.json');local=harness.read(root/'local/summary.json');b=summary['baseline']
  candidates=[]
  for step in range(1,4):
   folder=raw/'steps'/f'{step:03}';r=harness.read(folder/'evaluation/result.json');code=(folder/'candidate.lean').read_text();m=harness.metrics(r)
   log=(folder/'evaluation/fixed/check.log').read_text();errors=re.findall(r'(?m)^.*error:.*$',log)
   c={'step':step,'valid':r['valid'],'proof':proof_body(code,problem['statement']).strip(),'tokens':r['tokens'],'metrics':m,'local_final_score':score(m,b) if m else None,'first_error':errors[0] if errors else None,'diagnostics_file':str((folder/'evaluation/fixed/check.log').relative_to(REPO))}
   c['diagnostics']=diagnostics(log);c['bounded_feedback']=bounded_feedback(log)
   c['common_feedback']=harness.read(folder/'event.json')['state_after']['latest']['feedback']
   candidates.append(c)
   cards.append(f'<details><summary>P{n} · 후보 {step} · {"통과" if r["valid"] else "실패"} · {r["tokens"]} tokens</summary><pre>{html.escape(c["proof"])}</pre><p>{html.escape(" / ".join(errors[:3]))}</p><details><summary>원문 진단 앞부분</summary><pre>{html.escape(log[:7000])}</pre></details></details>')
  before=summary['state']['best'];after=local['after'];final=local['final']
  selection_score=score(after,b);final_score=score(final,b)
  info={'id':n,'name':problem['name'],'statement':problem['statement'],'baseline':b,'raw_selected':before,'post_local_selected':after,'final_recheck':final,'raw_selection_score':score(before,b),'local_selection_score':selection_score,'final_recheck_score':final_score,'score_gain_from_local':selection_score-score(before,b),'raw_common_cost':cost(before,b),'local_common_cost':cost(after,b),'selected_changed':before['sha256']!=after['sha256'],'candidates':candidates,'local_outcomes':dict(collections.Counter(a['outcome'] for a in local['attempts'])),'local_attempts':len(local['attempts']),'final_valid':local['final_valid'],'versions_checked':problem['version_info'],'selected_response':{'proof':proof_body(after['code'],problem['statement']).strip()},'arena_submission':{'name':problem['name'],'proof':after['code']},'raw_record_replay':harness.read(root/'raw-record-replay.json')}
  report['problems'].append(info);exports.append(info['arena_submission']);write(HERE/f'p{n}.response.json',info['selected_response'])
  table.append(f'<tr><td>P{n}</td><td>{b["tokens"]} → {before["tokens"]} → {after["tokens"]}</td><td>{b["raw_heartbeats"]/1000:.3f} → {before["raw_heartbeats"]/1000:.3f} → {after["raw_heartbeats"]/1000:.3f}</td><td>{score(before,b):.3f} → {selection_score:.3f}</td><td>{final_score:.3f}</td></tr>')
 write(HERE/'refactoring_results.json',report);write(HERE/'arena_submission.json',exports)
 (HERE/'arena_submission.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in exports))
 allout=collections.Counter(a['outcome'] for n in (1,2) for a in harness.read(REPO/'runs/repair-bridge-2026-10-27'/str(n)/'local/summary.json')['attempts'])
 valid=sum(c['valid'] for p in report['problems'] for c in p['candidates'])
 mean0=sum(p['raw_selection_score'] for p in report['problems'])/2;mean1=sum(p['local_selection_score'] for p in report['problems'])/2
 text=f'''# 공용 하네스 × 검증·수리 에이전트 — P1·P2

2026-10-27 · 고정 후보 6개 · 별도 모델 API 호출 0회 · 공식 평가 아님

공용 하네스 revision: `{report['provenance']['upstream_harness_commit']}`.
실제 패키지는 `src/lean_agent`이다. 핵심 코드는 수정하지 않았다.

## 실제 결과

- 최초 후보 {valid}/6 통과. 실패를 만들기 위한 mutation은 사용하지 않았다.
- 로컬 시도 결과: {dict(allout)}.
- 수리·정리 전후 평균 선택 점수: **{mean0:.3f} → {mean1:.3f}**.
- 두 최종 후보 모두 전체 원문 문맥에서 재검증했다. 지정 환경은 각각 Lean 4.26.0 하나이다.
- `refactoring_results.json`에는 모든 후보·측정·선택·로그 경로를, `p1.response.json`과 `p2.response.json`에는 공용 하네스가 받는 정확한 `{{"proof":"by ..."}}`를 넣었다.
- `arena_submission.json` / `.jsonl`의 proof는 명제를 포함한 전체 선언이다. 모델 응답 JSON과 혼동하면 안 된다. 대회에는 전송하지 않았다.

## 실험 구분

원본과 이번 대화에서 사전에 고정한 3가지 전략(귀납+광범위 simp, 구조적 subset 결합, 보수적 수정)을 비교했다. 과거 P1/P2 작업을 이미 본 상태이며 두 번째 전략은 과거 증명에서 정보를 얻었다. 따라서 새 모델의 독립 성능, blind 평가 또는 기존 35.238 평균과 직접 비교하는 실험이 아니다. 실행 중 후보를 LLM으로 재작성하지 않았다.

기존 수리의 원칙(명제 고정, 제한된 로컬 tactic, query→명시화→재검증, 원본/최선 보존, policy 프롬프트 출력)을 어댑터 후처리에 연결했다. 이번 post-pass는 전체 본문의 남은 목표 처리와 독립 한 줄 삭제/명시화를 사용한다. 지난 AST minimizer 전체를 이식하거나, 의미적 dependency 분석·trusted goal-state 수집을 구현한 것은 아니다.

## 하네스 분석

1. `harness.run(..., evaluator=...)` 확장점으로 `PreparedEvaluator`를 연결했다. 기본 CLI는 의존성이 있는 프로젝트를 거부하므로 Strata 준비 환경을 명시적으로 연결한다. 기존 작업 checkout을 수정하지 않고 별도 사본을 준비했다.
2. 입력·응답·코드·실행 로그와 선택 과정을 저장한다. core의 record replay도 통과해야 한다. replay는 Lean 재실행이 아니다.
3. 검증과 측정은 분리된다. 변경하지 않은 imports로 전체 파일을 먼저 검사하고, 새 프로세스 3회 raw heartbeat 중앙값을 측정한다.
4. 공용 점수는 `0.5*(L/L0 + H/H0)`를 최소화한다. 이번처럼 robustness=1이면 기존 local final score는 `100 - (200/3)*cost`이므로 순위가 같다. 여러 버전에서는 별도 통합이 필요하다.
5. 공용 공리 허용 목록은 propext/Classical.choice/Quot.sound이다. 어댑터에는 기존 정책대로 원본 공리의 부분집합 검사도 추가했다.
6. 준비 환경의 Lean 소스·컴파일 산출물·의존성 파일을 해시하고 실행 전후를 비교했다. 외부 환경이 core snapshot에 완전히 내장된 것은 아니므로 다른 컴퓨터에서는 동일 환경을 재준비해야 한다.

## 관측에서 얻은 개선 방향

- P1 실패 로그는 6,186자인데 공용 피드백은 마지막 4,000자 기반이어서 최초 quant 분기가 누락됐다. `diagnostics.py`는 첫 오류와 goal을 보존한다. P2에서는 이 누락이 관측되지 않았다. 원문 로그는 계속 보관한다.
- `simp_all [List.Subset, ...]`는 subset 목표를 원소 membership과 논리식으로 바꾼다. 이후 List.Subset.app를 적용하는 연산은 목표 형태와 맞지 않을 수 있다. 다음 정책은 목표가 subset인지, 이미 forall/implication/disjunction인지 먼저 구분해야 한다.
- 아직 shape 판별 스케줄러, 분기별 goal 인증, grind 기반 수리 등은 구현·평가하지 않았다. 이번 결과를 근거로 효과를 보장하지 않는다.
- 기존 escalation의 status/proof_body 계약을 공용 proof 계약으로 바꾸는 `protocol.py`를 추가했다. need_context/no_candidate는 후보 증명으로 잘못 제출하지 않는다. 모델 응답 실행은 하지 않았다.
- 공용 선택기는 동일 종합비율일 때 토큰·해시로 동점을 깬다. 기존 정책의 엄격한 개선/원본 유지와 다르다. 이번에는 동점 교체가 관측되지 않았다.
- 공용 최종 재검증이 실패하면 자동으로 차선 후보/원본을 재검증하는 경로가 없다. 이번에는 최종 실패가 없었지만, 수리 에이전트를 운영에 붙이기 전 보강할 부분이다.

## 재현

저장소 루트에서 실행한다. 기존 warm-up 원본과 Strata 4.26 checkout/build가 workspace에 필요하다.

```sh
python3 experiments/repair-bridge-2026-10-27/setup.py
python3 experiments/repair-bridge-2026-10-27/bridge.py 1 2
python3 experiments/repair-bridge-2026-10-27/local_pass.py 1 2
python3 experiments/repair-bridge-2026-10-27/export_policy.py
python3 experiments/repair-bridge-2026-10-27/report.py
PYTHONPATH=src python3 -m unittest discover -s tests -p test_harness.py -v
python3 experiments/repair-bridge-2026-10-27/test_bridge.py
```

완료한 run은 재사용한다. 독립 반복에는 실행 디렉터리 이름을 바꾸고 새 기록을 생성해야 한다. 중간 실패한 run을 지우거나 덮어쓰지 않는다. 생성된 무거운 실행 기록은 `runs/repair-bridge-2026-10-27`, 환경은 `artifacts/repair-bridge`에 있다.
'''
 if followup:
  text+='\n## JSON 진단 후속 실험\n\n위치 없는 plain-text 제안 2건을 Lean --json으로 다시 수집했다. 두 명시적 증명이 전체 재검증에 통과했지만 최종 선택을 이기지는 못했다. 이는 solver 성공률 개선이 아니라 제안 수집 손실을 복구한 결과다. 첫 고정 18회 처리와 분리한 탐색적 후속 실험이며 query_upgrade.py에 재현 코드가 있다.\n\n개발 중 부가 기록을 이미 봉인된 raw 디렉터리에 추가하려던 저장 충돌은 부가 기록을 밖으로 옮겨 해결했다. JSON 후속 실험에서 반복된 동일 tactic 문자열을 유일하다고 가정한 첫 probe는 위치 assertion에서 중단되었고, 실제 source offset으로 교체하도록 고쳤다. 해당 pilot 로그는 json-query-followup-position-pilot에 보존했으며 최종 실험 횟수에 섞지 않았다.\n'
 (HERE/'README.md').write_text(text)
 body=f'''<header><span class="tag">검증·수리 실험 · 2026.10.27</span><h1>공용 하네스에<br>로컬 수리를 연결하면?</h1><p>Warm-up 1·2번 · 실제 Lean 실행 · 실패를 강제로 만들지 않은 고정 후보 6개</p></header>
 <div class="metrics"><article><strong>{valid}/6</strong><span>최초 후보 검증 통과</span></article><article><strong>{mean0:.3f} → {mean1:.3f}</strong><span>평균 로컬 선택 점수 · 높을수록 좋음</span></article><article><strong>0회</strong><span>별도 모델 API 호출</span></article></div>
 <section><h2>1. 무엇을 연결했나</h2><p>공용 하네스의 입력·선택·기록 로직은 그대로 사용했다. <code>run(evaluator=...)</code>에 Strata 준비 환경 어댑터를 연결하고, 최초 후보 평가 뒤 제한된 자동 수리·정리를 적용했다.</p><div class="flow">JSON 후보 → 전체 Lean 검증 → 남은 목표 수리 / 한 줄 정리 → 전체 재검증·3회 계측 → 최선 보존 → 최종 재검증</div><p class="note">모델 응답은 proof 본문 하나이다. 명제·imports·주변 원문은 고정했다. 이전에 본 문제이며 역사적 증명에서 얻은 전략을 포함한다. 독립 모델 성능평가는 아니다.</p></section>
 <section><h2>2. 실제 점수</h2><div class="table"><table><thead><tr><th>문제</th><th>토큰: 원본 → 후보 선택 → 로컬 후</th><th>HB / 1000: 같은 순서</th><th>선택 점수: 전 → 후</th><th>최종 재검증 점수</th></tr></thead><tbody>{''.join(table)}</tbody></table></div><p>선택 점수는 탐색 중 측정한 값, 최종 재검증 점수는 선택 뒤 새 프로세스에서 다시 측정한 값이다. 작은 HB 차이를 별도의 개선으로 주장하지 않는다.</p><p>공용 cost = ½ × (토큰 비율 + HB 비율), 작을수록 좋음. 두 문제의 robustness가 1이므로 로컬 final score = 100 − ⅔ × 100 × cost. 공식 서버 점수는 아니다.</p></section>
 <section><h2>3. 후보와 원문 오류를 직접 보기</h2><p>각 문제에서 ① 귀납+넓은 단순화 ② 구조적인 subset 결합 ③ 보수적인 수정 순으로 고정했다. 실패가 나오더라도 LLM으로 다시 고치지 않았다.</p>{''.join(cards)}</section>
 <section><h2>4. 로컬 처리 결과</h2><p>{html.escape(str(dict(allout)))}</p><p>실패 후보에는 남은 목표에 assumption/rfl/exact?/simp? 및 고정된 subset 조합을 시도했다. P1에서는 quant/app/ite/eq 같은 분기에 목표가 남았고, P2에서도 같은 종류의 목록 포함 추론이 남았다. 유효 후보에는 지원되는 독립 한 줄의 삭제·simp 명시화를 시도했다. query 실행 자체는 최종 후보에서 제외하고, 한 줄 제안을 추출했을 때만 다시 전체 검증했다.</p><div id="observations"><p><b>선택 효과와 로컬 성공은 다르다.</b> 보수적인 긴 증명에서 한 줄을 줄여 검증에 성공해도 이미 더 좋은 후보가 있으면 최종 선택은 바뀌지 않는다. 따라서 valid 시도 수와 최종 점수 증가를 별도로 기록했다.</p><p>첫 번째 짧은 후보들은 귀납 뒤 넓은 단순화만으로 목표를 닫지 못했다. 뒤에 solver를 붙이는 방식은 앞선 구조적 선택을 복구하는 데 한계가 있다. 상세 원문 진단은 위에서 확인할 수 있다.</p><p><code>diagnostics.py</code>는 첫 오류·위치·goal 텍스트를 보존하는 결정적 피드백을 만든다. 이것은 실제 tactic-state 인증과 다르며, 기존 공용 루프의 피드백을 이번 실험 중 교체하지는 않았다.</p></div></section>
 <section><h2>남은 목표를 사람 말로 풀면</h2><p>P2의 quant 분기에 남은 목표는 아래와 같은 구조다. 실제 진단의 긴 타입·변수 이름만 줄여 썼다.</p><pre>가설 1: x가 A에 있으면 x는 A′에도 있다.
가설 2: x가 B에 있으면 x는 B′에도 있다.
목표: x가 A 또는 B에 있으면, x는 A′ 또는 B′에 있다.</pre><p>사람은 “A인 경우 / B인 경우”를 나눠 해당 가설을 적용한다. 하지만 넓은 simp만으로 이 추론이 끝나지는 않았다. subset을 너무 일찍 펼치면 기존 subset 결합 연산도 바로 적용하기 어렵다. 연산을 더 많이 반복하는 것보다 현재 목표 형태에 맞게 선택하는 것이 다음 실험 과제다.</p></section>
 <section><h2>5. 다음에 바꿀 부분</h2><ol><li><b>오류 앞부분과 goal을 보존:</b> 공용 평가기는 긴 로그의 마지막 4,000자만 오류에 담는다. 실제 P1의 6,186자 로그에서 최초 quant 분기가 공용 피드백에서 사라졌다. 추가한 diagnostics.py는 그 첫 목표를 보존한다. P2에서는 같은 누락이 관측되지 않았다.</li><li><b>명세·정의 문맥 연결:</b> 모델 요청에는 문제와 이전 피드백은 있지만 전체 template·import된 정의 본문이 자동으로 들어가지 않는다. 로컬 검색 결과를 명시적으로 공급해야 한다.</li><li><b>진단에 맞는 수리 선택:</b> 이미 실패한 tactic 뒤에 solver를 붙이는 방법은 구조적인 잘못을 복구하지 못할 수 있다. 블록 재작성과 분기·귀납 선택은 별도 문제다.</li><li><b>제안 위치와 다중 goal 구분:</b> 한 줄 query 제안을 보수적으로 추출한다. 여러 goal의 제안들을 하나의 script라고 합쳐 제출하지 않는다.</li><li><b>프로토콜 어댑터:</b> 기존 escalation은 status/proof_body를 반환하도록 요청하지만 공용 하네스는 proof 하나만 받는다. candidate만 변환하고 need_context/no_candidate는 별도 제어 신호로 처리해야 한다.</li><li><b>최종 실패 fallback:</b> 공용 코드가 마지막 검증 실패를 표시하기는 하지만 자동으로 차선 후보를 다시 검증해 반환하지는 않는다. 이번에 관측된 실패가 아닌 코드상 개선 지점이다.</li></ol></section>
 <section><h2>6. 결과 파일</h2><p><a href="refactoring_results.json">전체 결과 JSON</a> · <a href="p1.response.json">P1 모델 응답 JSON</a> · <a href="p2.response.json">P2 모델 응답 JSON</a> · <a href="arena_submission.json">Arena 형식 JSON</a> · <a href="README.md">재현 README</a> · <a href="escalation/p1.prompt.txt">P1 수리 요청 프롬프트</a> · <a href="escalation/p2.prompt.txt">P2 수리 요청 프롬프트</a></p><p>LLM escalation은 프롬프트 출력까지만 수행한다. 외부 모델에 전송하거나 대회에 제출하지 않았다.</p></section>'''
 if followup:
  recovered=sum(x['outcome']=='valid' for x in followup['results'])
  extra=f'<section><h2>후속 실험: JSON 진단으로 제안 복구</h2><p>일반 텍스트에는 위치가 없었던 제안 2건을 Lean의 JSON 진단으로 다시 받았다. <b>{recovered}/2 명시적 증명이 전체 검증에 통과</b>했다. solver가 새로 해결한 문제가 아니라, 이미 나온 제안을 안전하게 회수한 것이다.</p><pre>simp? at m    → simp only at m\nsimp? at name → simp only at name</pre><p>두 후보 모두 기존 최선보다 점수가 낮아 최종 선택은 유지했다. 고정된 18회 로컬 처리와 구분한 탐색적 후속 실험이다.</p></section>'
  body=body.replace('<section><h2>5. 다음에 바꿀 부분</h2>',extra+'<section><h2>5. 다음에 바꿀 부분</h2>')
 css='''*{box-sizing:border-box}body{margin:0;background:#f3f5f7;color:#192d3d;font:17px/1.75 system-ui,-apple-system,sans-serif}main{max-width:1180px;margin:auto;padding:48px 26px 80px}header{padding:36px 0}h1{font-size:52px;line-height:1.18;letter-spacing:-2px;margin:20px 0}h2{font-size:26px}.tag{color:#146e65;font-weight:750}.metrics{display:grid;grid-template-columns:1fr 2fr 1fr;gap:16px}.metrics article,section{background:white;border:1px solid #dce4e8;border-radius:16px;padding:26px;margin-bottom:22px}.metrics strong{font-size:30px;display:block;color:#156e63}.metrics span{font-size:14px}p{margin:14px 0}pre{background:#142735;color:#e4edf4;padding:20px;border-radius:9px;white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 ui-monospace,monospace}details{border-top:1px solid #dce4e8;padding:14px 0}summary{cursor:pointer;font-weight:650}.flow{padding:22px;background:#e9f4f0;border-radius:10px}.note{font-size:15px;color:#596a76}.table{overflow-x:auto}table{border-collapse:collapse;min-width:850px;width:100%;font-size:15px}th,td{padding:12px;text-align:left;border-bottom:1px solid #dce4e8}a{color:#066d9a}li{padding:8px 0}code{font-size:.9em} @media(max-width:700px){h1{font-size:36px}.metrics{grid-template-columns:1fr}main{padding:20px 14px}}@media print{body{background:white}section{break-inside:avoid}main{padding:0}}'''
 (HERE/'report.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>공용 하네스 × 검증·수리</title><style>'+css+'</style><main>'+body+'</main></html>')
 print(json.dumps({'valid_initial':valid,'outcomes':dict(allout),'mean_before':mean0,'mean_after':mean1},ensure_ascii=False))
if __name__=='__main__':generate()
