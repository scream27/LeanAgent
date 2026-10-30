"""Render a self-contained Korean report from measured results and reviewed notes."""
import json,html
from pathlib import Path
H=Path(__file__).resolve().parent
E=lambda s:html.escape(str(s))
LABELS={'direct positivity and contradiction':'양수성과 마지막 모순 직접 증명','remove repeated nlinarith hypotheses':'nlinarith 중복 가정 제거','restrict nlinarith to explicit premises':'nlinarith only로 가정 제한','canonical le_top proof':'부등식 증명을 le_top으로 치환','narrow derivative simplification':'미분식 simp를 simp only로 제한','batch adjacent rewrites':'연속된 rw 묶기','replace repeated rewrite traversal':'repeat rw를 simp only로 치환','remove unused dependent predicate arguments':'지역 명제의 의존 인자 삭제','narrow linearity simplification':'선형성 분기 simp_all 범위 제한'}
def main():
 d=json.loads((H/'results.json').read_text());c=d['comparison'];p=d['problems'];board=d['leaderboard'];notes=json.loads((H/'observations.json').read_text())
 valid=sum(x['valid'] for r in p for x in r['candidates']);total=sum(len(r['candidates']) for r in p)
 parts=['''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>공용 하네스 확장 검증 — P4·P5·P6</title><style>
:root{color-scheme:light;--ink:#172a3a;--muted:#526675;--teal:#006d77;--line:#d7e2e8}*{box-sizing:border-box}body{margin:0;background:#f3f6f8;color:var(--ink);font:17px/1.75 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}main{max-width:1120px;margin:auto;padding:54px 28px 90px}h1{font-size:42px;line-height:1.25;margin:14px 0 24px}h2{font-size:27px;margin-top:0}h3{font-size:21px}p{max-width:880px}.eyebrow{color:var(--teal);font-weight:750;letter-spacing:.06em}.lead{font-size:21px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card,section{background:white;border:1px solid var(--line);border-radius:18px;padding:28px;margin:24px 0}.grid .card{margin:0}.big{display:block;font-size:35px;font-weight:750;color:var(--teal)}.muted{color:var(--muted);font-size:15px}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:15px}th,td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#edf4f6;white-space:nowrap}td.num{text-align:right;font-variant-numeric:tabular-nums}pre{background:#132630;color:#e6f1f4;padding:18px;border-radius:10px;overflow:auto;white-space:pre-wrap;word-break:break-word;font:13px/1.6 ui-monospace,monospace}summary{cursor:pointer;font-weight:650;padding:12px 0}details{border-top:1px solid var(--line)}.callout{border-left:4px solid var(--teal);padding:10px 20px;background:#edf7f7}.bad{color:#a53730}.good{color:#006d57}a{color:var(--teal)}code{font-size:.9em;overflow-wrap:anywhere}.tag{padding:3px 8px;border-radius:6px;background:#edf4f6;white-space:nowrap}@media(max-width:700px){main{padding:24px 14px}h1{font-size:31px}.grid{grid-template-columns:1fr}section{padding:19px}th,td{padding:10px}}@media print{body{background:white}main{padding:0}section{break-inside:avoid}details{display:block}}</style><main>
<div class="eyebrow">LEAN REFACTOR ARENA · 2026.10.27</div><h1>짧게 고쳤다고,<br>좋은 증명이 되는 것은 아니다</h1><p class="lead">공용 하네스의 검증 범위를 1·2번에서 4·5·6번으로 확장했다. 실제 후보의 실패 원인, 통과 후 점수, 상위권과의 차이를 함께 살펴본다.</p>''']
 parts.append(f'<div class="grid"><div class="card"><span class="big">{valid} / {total}</span>새 후보 검증 통과</div><div class="card"><span class="big">3 / 3</span>최종 선택 재검증 통과</div><div class="card"><span class="big">0</span>유료 API 호출</div></div>')
 parts.append('<section><h2>무엇을 실행했나</h2><p>이 대화에서 미리 작성한 후보를 문제당 3개씩 고정하고, 공용 하네스의 fixture 입력으로 실행했다. 실시간 모델의 생성 성능 실험은 아니다. 검증 결과를 보고 후보를 몰래 바꾸지 않았고, 의도적으로 실패시키는 변형도 넣지 않았다.</p><p>원본 파일의 문맥과 정리 statement를 보존했다. 먼저 계측 코드를 넣지 않은 전체 파일을 컴파일한 뒤, 목표 정리만 3회 새 프로세스에서 계측했다. 기존 공리보다 새 공리가 추가되면 거절하며, 점수 기준으로 원본보다 좋은 후보만 선택한다.</p><p class="muted">공용 하네스 ba593fc · Physlib c484336 · Lean 4.32.0. 세 문제는 데이터에 지정된 버전이 각각 하나여서 이 실행으로 세 문제의 버전 조건을 모두 검사했다. source token = lean-source-anchored-v1, heartbeat = raw counter 중앙값 ÷ 1,000.</p></section>')
 parts.append('<section><h2>실제 최종 점수</h2><p class="callout">로컬 final score = (토큰 감소율 + heartbeat 감소율 + 버전 통과율) ÷ 3. 원본이 모두 통과하면 33.333점이다. 여기의 점수는 공식 서버 제출 점수가 아니다.</p><div class="scroll"><table><tr><th>문제</th><th>선택</th><th>토큰 원본 → 최종</th><th>HB 원본 → 최종</th><th>final score</th><th>원본 대비</th></tr>')
 for r in p:
  b=r['baseline'];f=r['final'];a=r['final_axes'];sel='원본 fallback' if r['fallback'] else '후보 '+str(r['selected_candidate'])
  parts.append(f'<tr><td>P{r["id"]}</td><td>{sel}</td><td>{b["tokens"]} → {f["tokens"]}</td><td>{b["raw_heartbeats"]/1000:,.3f} → {f["raw_heartbeats"]/1000:,.3f}</td><td><b>{a["score"]:.3f}</b></td><td>{a["score"]-100/3:+.3f}</td></tr>')
 parts.append('</table></div><p class="muted">최종 점수는 선택 단계의 수치를 재사용하지 않고 최종 재검증 수치로 계산했다. 미세한 heartbeat 차이는 반복 계측 변동과 함께 읽어야 한다.</p></section>')
 for r in p:
  parts.append(f'<section><h2>P{r["id"]} · {E(notes[str(r["id"])]["title"])}</h2><p class="muted"><code>{E(r["name"])}</code></p><p>{E(notes[str(r["id"])]["interpretation"])}</p><div class="scroll"><table><tr><th>후보 / 전략</th><th>검증</th><th>토큰</th><th>HB 감소</th><th>후보 점수</th></tr>')
  for x in r['candidates']:
   a=x['axes'];m=x['metrics'];status='통과' if x['valid'] else '실패'
   parts.append(f'<tr><td>C{x["candidate"]} · {E(LABELS.get(x["strategy"],x["strategy"]))}</td><td class="{"good" if x["valid"] else "bad"}">{status}</td><td>{m["tokens"] if m else "—"}</td><td>{f"{a['heartbeat_reduction']:+.2f}%" if a else "—"}</td><td>{format(a["score"],".3f") if a else "선택 제외"}</td></tr>')
  parts.append('</table></div>')
  for x in r['candidates']:
   parts.append(f'<details><summary>C{x["candidate"]} 변경 diff / 실제 오류</summary><pre>{E(x["diff"])}</pre>')
   for er in x['diagnostics']:parts.append('<pre>'+E(er['message'])+'</pre>')
   parts.append('</details>')
  parts.append('</section>')
 parts.append('<section><h2>검증기 자체에서 드러난 문제</h2>')
 for para in notes['instrumentation']:parts.append('<p>'+E(para)+'</p>')
 parts.append('</section><section><h2>상위권과는 얼마나 다른가</h2><p>공식 closed-model 공개 리더보드를 2026-10-27에 조회했다. 표는 전체 warm-up 15문제 평균이며, 모델명은 참가자의 자기 보고다.</p><div class="scroll"><table><tr><th>참가자</th><th>점수</th><th>토큰 감소</th><th>HB 감소</th><th>버전 통과</th></tr>')
 for b in board[1:4]:parts.append('<tr>'+''.join('<td>'+E(b[i])+'</td>' for i in (1,3,4,5,6))+'</tr>')
 parts.append(f'</table></div><p>우리의 이전 15문제 Local Minimizer 실험은 <b>{c["previous_fifteen_mean"]:.3f}점</b>이었다. 이번 공용 하네스에서 확인한 1·2·4·5·6번만의 평균은 <b>{c["measured_five_mean"]:.3f}점</b>이다. 이 둘은 서로 다른 실험이며, 5문제 평균을 전체 리더보드 점수로 읽으면 안 된다.</p><p>참고로 기존 15문제 결과의 해당 5개 행만 교체한 혼합 추정은 <b>{c["mixed_fifteen_projection"]:.3f}점</b>이다. 재실행하지 않은 10문제의 과거 수치가 섞였으므로 공식 점수나 새 전체 실험 결과가 아니다.</p><p class="callout">현재의 5개 점수를 고정하면 나머지 10문제를 모두 100점으로 만든다는 극단적인 가정에서도 전체 평균은 {c["fixed_five_remaining_perfect_upper_bound"]:.3f}점이다. 상위권에 접근하려면 이미 검증된 5문제도 더 크게 개선해야 한다.</p><p>상위권은 토큰과 heartbeat를 함께 약 90% 줄였다. 우리의 1·2번은 토큰을 약 81–85% 줄였지만 heartbeat 감소는 약 7–10%였다. 짧은 자동화 전술로 긴 코드를 대체하는 것만으로는 이 차이를 메우기 어렵다. 상대 참가자의 문제별 증명은 확보하지 못했으므로 어떤 기법을 썼는지는 추정하지 않는다.</p></section>')
 parts.append('<section><h2>LLM 없이 우선 개선할 부분</h2>')
 for title,body in notes['recommendations']:parts.append('<h3>'+E(title)+'</h3><p>'+E(body)+'</p>')
 parts.append('</section><section><h2>직접 확인할 자료</h2><p><a href="results.json">전체 결과 JSON</a> · <a href="arena-submission.json">선택한 증명 JSON</a> · <a href="candidate-freeze.json">후보 고정 기록</a> · <a href="leaderboard/closed.html">조회 당시 리더보드</a> · <a href="README.md">재현 절차</a></p><p><a href="https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena">공식 Arena</a> · <a href="https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/tree/ba593fc4357ee5c429b8f28f1aac512d05bb4355/src/lean_agent">사용한 공용 하네스</a></p><p class="muted">공식 채점 워커와 실행 환경·계측 경계가 완전히 같다고 보장하지 않는다. 후보는 기존 문제를 알고 작성했으므로 블라인드 테스트나 모델 간 비교 결과가 아니다. 검증 실패 후보는 제출 JSON에 포함하지 않는다.</p></section></main></html>')
 (H/'report.html').write_text(''.join(parts))
if __name__=='__main__':main()
