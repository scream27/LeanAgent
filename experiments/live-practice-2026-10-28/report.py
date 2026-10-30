"""Readable progress/final report; pending problems never masquerade as failures."""
import json,html,collections,statistics
from pathlib import Path
from status import main as update_status
H=Path(__file__).resolve().parent;R=H.parents[1];E=lambda s:html.escape(str(s))
def main():
 update_status();d=json.loads((H/'progress.json').read_text());m=json.loads((H/'manifest.json').read_text());completed=[x for x in d['rows'] if x['status']=='complete'];attempts=[s for x in d['rows'] for s in x['steps']];failed=[s for s in attempts if not s['valid']]
 out=['<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>공용 하네스 실시간 모델 연결 실험</title><style>body{margin:0;background:#f3f6f9;color:#163044;font:17px/1.75 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}main{max-width:1100px;margin:auto;padding:40px 24px}h1{font-size:36px;line-height:1.3}h2{font-size:25px}section{background:white;border:1px solid #dae3eb;border-radius:16px;padding:24px;margin:24px 0}.muted{color:#5b7180;font-size:14px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:10px;border-bottom:1px solid #dde5e9;vertical-align:top}th{background:#edf4f8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#142c3c;color:#edf5fa;padding:16px;border-radius:8px;font:13px/1.6 monospace}details{border-top:1px solid #dde5e9;padding:12px 0}summary{cursor:pointer;font-weight:650}a{color:#006e88}.scroll{overflow:auto}.banner{background:#e5f3f0;padding:20px;border-left:5px solid #168576}</style><main><p class="muted">LIVE MODEL RELAY · 시작 2026-10-28 · 갱신 2026-10-30</p><h1>LLM 응답은 이 대화가,<br>검증과 선택은 공용 하네스가</h1>']
 terminal=[x for x in d['rows'] if x['status'] in ('complete','baseline_rejected','final_verification_failed')]
 blocked=sum(x['status']=='baseline_rejected' for x in d['rows']);final_failed=sum(x['status']=='final_verification_failed' for x in d['rows'])
 out.append(f'<p class="banner">주 버전 처리 {len(terminal)}/29개 · 최종 검증 통과 {len(completed)}개 · 원본 단계 차단 {blocked}개 · 최종 재검증 실패 {final_failed}개.<br>데이터셋 35개 행 · 모델 응답 {len(attempts)}회 중 거절 {len(failed)}회. 원본 검사 차단은 모델 실패와 분리한다.</p>')
 selections=json.loads((H/'selections.json').read_text())['unique_problems']
 scored=[r for r in selections if 'local_final_score' in r]
 fallback=sum(r.get('original_fallback',False) for r in selections)
 out.append(f'<section><h2>결과를 읽는 기준</h2><p>최종 검증 통과 {len(completed)}개 중 후보 선택 {len(completed)-fallback}개, 원본 fallback {fallback}개다. 전체 지정 버전까지 측정된 {len(scored)}개만의 평균 로컬 final score는 <b>{statistics.mean(r["local_final_score"] for r in scored):.3f}</b>점이다. 같은 집합의 원본 기준은 33.333점이다. 검증에 진입하지 못한 문제와 최종 실패는 이 평균에서 제외했으므로 전체 29문제 평균이나 대회 점수로 해석하면 안 된다.</p><p>최종 통과 16개는 지정 버전 검증까지 모두 끝났다. Cslib P8·9는 각 3개 버전, ArkLib P12는 4개 버전에서 동일 증명이 통과했다. 원본 fallback의 소수점 차이는 반복 계측 변동이다.</p></section>')
 if completed:
  gains=[]
  for x in completed:
   b=x['summary']['baseline'];f=x['summary']['final'];g=100*(2-f['tokens']/b['tokens']-f['raw_heartbeats']/b['raw_heartbeats'])/3;gains.append((g,x['id'],x['name']))
  out.append('<section><h2>확인된 개선 사례</h2><p>아래 수치는 최종 재검증과 지정 버전 검증까지 통과한 문제의 로컬 final score다. 원본은 약 33.333점이며, 전체 데이터셋이나 공식 리더보드 평균을 뜻하지 않는다.</p><ul>')
  for gain,n,name in sorted(gains,reverse=True)[:4]:out.append(f'<li>P{n} {E(name)}: <b>{100/3+gain:.3f}점</b> · 원본 대비 {gain:+.3f}점</li>')
  out.append('</ul></section>')
 out.append('<section><h2>이전 실험과 달라진 점</h2><p>미리 만들어 둔 후보를 재생하지 않는다. 하네스가 원본·현재 최선 후보·직전 오류를 담아 요청하면, 현재 대화 모델이 그 내용을 읽고 새 응답을 전달한다. 응답은 해당 요청 해시에 연결된다. Lean 실행, 후보 선택, 호출 한도와 최종 재검증은 공용 하네스가 수행한다.</p><p>실행에는 준비된 프로젝트를 연결하는 환경 어댑터, 중단 후 이어가기, 문서 주석·계측 명령 경계 보정을 사용했다. 점수 함수와 후보 선택 규칙은 공용 하네스 그대로다. 입력 검사기의 오탐은 이번 기본 실행에서 완화하지 않고 실패로 기록했다.</p><p>문제당 최대 3응답. 프롬프트는 공용 하네스 예제의 원문을 유지했다. 모델 역할에서 프로젝트를 추가 검색하거나 별도 Lean 시험을 하지 않고 요청과 피드백으로 후보를 작성한다. 하네스 환경 준비는 별도의 실행 작업이다.</p><p class="muted">별도 API 호출 비용 0. 이 대화의 모델 사용량은 미측정이며 무료·0토큰으로 간주하지 않는다. 과거 문제 노출이 있는 같은 대화이므로 블라인드 모델 성능 평가가 아니다.</p></section>')
 from summarize_retries import main as summarize_retries
 summarize_retries();retry_data=json.loads((H/'posthoc-retries.json').read_text())
 out.append('<section><h2>LLM 없이 재시도한 별도 진단</h2><p>기본 실행에서 timeout이 난 세 건만, 코드를 한 글자도 바꾸지 않고 동일한 제한으로 한 번씩 다시 검사한다. 이는 사후 진단이며 기본 하네스의 실패 기록과 점수를 덮어쓰지 않는다. 추가 모델 호출은 0회다.</p><table><tr><th>대상</th><th>재검증</th><th>로컬 점수</th><th>기본 선택 점수 대비</th></tr>')
 for retry in retry_data['rows']:
  val=retry.get('local_final_score');gain=retry.get('score_gain_over_harness_selection');v='—' if val is None else f'{val:.3f}';g='—' if gain is None else f'{gain:+.3f}'
  out.append(f'<tr><td>P{retry["id"]} / {E(retry["stage"])}</td><td>{E(retry["status"])}</td><td>{v}</td><td>{g}</td></tr>')
 out.append('</table><p><a href="posthoc-retries.json">재시도 결과 JSON</a> · <a href="retry-selected-proofs.json">재시도 후 결정적으로 재선택한 증명 JSON</a> · 점수 차이에는 반복 계측 변동도 포함된다.</p></section>')
 out.append('<section><h2>재시도는 점수와 검증 가능 범위에 각각 기여했다</h2><table><tr><th>비교 대상</th><th>기본 실행</th><th>LLM 없는 재시도 후</th></tr><tr><td>같은 16문제의 평균 local final score</td><td>40.558</td><td>40.641</td></tr><tr><td>최종 검증된 고유 문제 수</td><td>16</td><td>17</td></tr><tr><td>회수된 P19를 포함한 17문제 평균</td><td>비교 불가: 기본 실행에서 P19 최종 timeout</td><td>41.403</td></tr></table><p>P15의 더 좋은 후보를 회수한 효과는 같은 16문제 평균에서 확인한다. P19는 검증 가능 문제를 하나 늘린 효과와 후보 선택 개선을 별도로 본다. 전체 29문제 중 12개는 여전히 원본 단계에서 차단됐으며, 이 17문제 평균에 포함되지 않는다.</p></section>')
 out.append('<section><h2>29문제 최종 결과</h2><p>원본과 최종 선택은 각각 새 Lean 프로세스 3회로 계측한다. 토큰은 공용 하네스의 proof-body source token이며 이전 o200k_base 모의 실험이나 모델 API 토큰과 다르다. 이 표의 감소율은 주 버전 기준이다. 주 버전 점수 = 100 × (토큰 감소 비율 + HB 감소 비율 + 1) / 3. 원본 기준은 33.333점이다. 최종 통과한 16개는 지정 버전 모두에서 통과했으므로 robustness=1이며 아래 값은 로컬 final score와 같다. 원본 검사 차단·최종 실패에는 점수를 임의로 부여하지 않았다.</p><div class="scroll"><table><tr><th>ID / 문제</th><th>상태 / 선택</th><th>후보 통과/응답</th><th>토큰 감소</th><th>HB 감소</th><th>로컬 final score</th><th>버전 통과</th></tr>')
 for x in d['rows']:
  l=h=score='—';choice='';s=x['summary']
  if s and s['final_valid']:
   b=s['baseline'];f=s['final'];l=f"{100*(1-f['tokens']/b['tokens']):.2f}%";h=f"{100*(1-f['raw_heartbeats']/b['raw_heartbeats']):.2f}%"
  if s and s['final_valid']:
   original=next(item['row']['src'] for item in m['problems'] if item['id']==x['id']);choice=' · 원본 유지' if s['state']['best']['code'].strip()==original.strip() else ' · 후보 선택'
  if s and s['final_valid']:score=f"{100*(3-f['tokens']/b['tokens']-f['raw_heartbeats']/b['raw_heartbeats'])/3:.3f}"
  out.append(f'<tr><td>{x["id"]}. {E(x["name"])}</td><td>{E(x["status"])}{choice}</td><td>{sum(t["valid"] for t in x["steps"])}/{len(x["steps"])}</td><td>{l}</td><td>{h}</td><td>{score}</td><td>{x["compatibility"]["passed"]}/{x["compatibility"]["required"]}{"" if x["compatibility"]["all_measured"] else " · 미측정"}</td></tr>')
 out.append('</table></div></section><section><h2>모델이 실제로 받은 오류</h2><p>후보 거절 13건의 구조화된 진단은 compile 10건, timeout 3건이다. timeout은 증명이 틀렸다는 판정이 아니다. <a href="failure-routing.json">LLM 없는 오류 분류·처리 경로</a></p><p>아래는 후보 검증 실패다. 하네스가 오류를 탐지해 다음 요청으로 전달한 것이므로, 그 자체가 하네스 구현 결함을 뜻하지 않는다.</p>')
 for x in d['rows']:
  for t in x['steps']:
   if not t['valid']:out.append(f'<details><summary>P{x["id"]} · 응답 {t["step"]} · {E(t["feedback"]["status"])}</summary><pre>{E(t["feedback"]["details"])}</pre></details>')
 out.append('</section><section><h2>하네스·환경 실패 원문</h2><p>보정 후 성공하더라도 최초 실패 기록을 지우지 않는다. 모델 응답 전 원본 검증에서 멈춘 사례는 모델 실패율에 넣지 않는다.</p>')
 for item in m['problems']:
  root=R/'runs/live-practice-2026-10-28'/str(item['id'])
  for raw in sorted(root.glob('raw*')):
   for p in sorted(raw.glob('baseline*/result.json')):
    v=json.loads(p.read_text())
    if not v['valid']:out.append(f'<details><summary>P{item["id"]} · {E(raw.name)} / {E(p.parent.name)} · 원본/계측 실패</summary><pre>{E(json.dumps(v,ensure_ascii=False,indent=2))}</pre></details>')
 out.append('</section><section><h2>검증 전에 걸러진 원인들</h2><table><tr><th>종류</th><th>관측</th><th>처리 방향</th></tr><tr><td>데이터 경계</td><td>P3에 다음 theorem 포함, P7에 다음 set_option 래퍼 포함</td><td>원시 데이터 경계를 수정하고 별도 실행으로 비교</td></tr><tr><td>검사기 오탐</td><td>P10·11의 정상적인 #D 집합 크기 표기를 금지</td><td>문자 검색을 Lean 구문 단위 검사로 교체</td></tr><tr><td>모듈 공리 검사</td><td>P27·28·29에서 일반 정리를 공리처럼 보고. 별도 #print axioms는 표준 공리만 출력</td><td>증명 본문이 보이는 환경에서 독립 공리 검사</td></tr><tr><td>원본 미완성 의존성</td><td>P14·17·18·20·22 대상 정리에 sorryAx 의존성</td><td>원본 문제로 격리; 모델 실패율에서 제외</td></tr><tr><td>설치 경로 해석</td><td>ArkLib 4.30의 Lake 경고를 --print-prefix 경로에 합쳐 FileNotFoundError</td><td>호환성 어댑터에서 stderr 분리 후 원본·후보 통과; 경고 로그 보존</td></tr><tr><td>실행 timeout</td><td>P15 후보, P19 후보·최종 검사, P18 원본 계측(재시도에서 sorryAx 확인)</td><td>구문·논리 오류로 단정하지 않고 제한된 재시도</td></tr></table><p><a href="input-preflight.json">전체 입력 사전 검사</a> · <a href="diagnostics/strata-axioms.log">Strata 독립 공리 검사 로그</a></p></section><section><h2>관측 결과와 수리 정책 제안</h2><p><b>긴 논리 단계를 기존 등식으로 대체한 사례.</b> P12는 두 몫 등식을 연결해 긴 후반 재구성을 제거했다. 토큰 638→193, heartbeat 약 51% 감소, final score 73.471이다. 추가 압축 시도는 존재하지 않는 상수 참조로 거절됐고 이전 검증 후보를 유지했다. 지정 4개 버전 모두 같은 코드로 통과했다.</p><p><b>원본도 먼저 검사해야 한다.</b> P14는 컴파일 성공 뒤 대상 정리의 sorryAx 의존성이 발견되어 모델 생성 전에 중단됐다. 단순 컴파일 성공을 완전한 증명으로 취급하면 놓치는 사례다.</p><p><b>오류 위치와 수정 위치는 다를 수 있다.</b> P23의 simp 병합은 goal 처리 순서를 바꾸었고, P5의 field_simp 제거는 뒤의 conv 경로를 깨뜨렸다. 오류 줄만 교체하기보다 변경 구간을 되돌려 검증하는 최소화가 유용하다.</p><p><b>탐색을 직접 증명으로 바꾸면 큰 개선이 가능하다.</b> P13에서는 부등식에 양수를 곱하는 단계를 nlinarith 대신 직접 정리로 증명해 heartbeat를 크게 줄였다. 향후 exact? 등의 제안을 명시적 proof로 고정하고 계측하는 실험이 적합하다.</p><p><b>원본 fallback은 유지한다.</b> P9·23·25는 후보를 시도했지만 원본이 최종 선택됐다. 기본 실행에는 별도의 로컬 수리를 덧붙이지 않았으므로, 이후 수리 에이전트의 효과를 비교할 원시 기준 자료로 사용할 수 있다.</p><p><a href="observations.md">근거별 관찰과 후속 실험 메모</a></p></section><section><h2>자료와 재현</h2><p><a href="repair-handoff.md">수리 에이전트 연결 계약과 파일 안내</a></p><p><a href="aggregate.json">집계 JSON 및 분모 설명</a></p><p><a href="per-dataset-results.json">35개 행별 결과 JSON</a> · <a href="repair-cases.jsonl">실제 실패 수리 입력 JSONL</a> · <a href="selections.json">최종 선택 증명 JSON</a> · <a href="progress.json">상태·측정 JSON</a> · <a href="manifest.json">데이터셋 해시와 중복 매핑</a> · <a href="README.md">실행 프로토콜</a></p><p class="muted">29문제 처리 및 최종 선택 증명의 추가 버전 감사 완료. 원본 단계에서 차단된 12개에는 후보 호환성을 주장하지 않는다. 공식 tokenizer·worker의 점수가 아니므로 리더보드와 직접 비교하지 않는다.</p></section></main></html>')
 (H/'report.html').write_text(''.join(out))
if __name__=='__main__':main()
