"""Evidence-backed explanations; no new Lean runs or repair success claims."""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def evidence(path, label):
    assert (ROOT / path).is_file(), path
    return f'<a href="../../{html.escape(path)}">{html.escape(label)}</a>'


def render():
    out = ['''<section id="current-time-policy"><h2>변경된 실행 정책: Lean 검증 시간제한 없음</h2><p class="banner"><b>앞으로 Lean 검증의 wall-clock 제한은 두지 않는다.</b> 설정은 <code>lean.timeout_seconds: null</code>이다. 완료될 때까지 기다리고, heartbeat는 기존처럼 측정해 후보 점수에 반영한다. 별도의 실행 시간 감점을 추가하지 않는다.</p><p>아래 180초는 대회 규정이 아니라 당시 실험에서 운영상 설정한 제한이다. 사용자 요청에 따라 제거했다. 기존 timeout 사례·재시도 점수는 이 과거 설정 아래의 기록으로 보존하며, 무제한 실행에서 retry 정책이 더 낫다는 근거로 일반화하지 않는다. 무제한 설정으로 29문제를 다시 실행한 결과는 아직 없다.</p><p>사용자가 중단한 실행이나 외부 프로세스 종료는 증명 오류와 구분한다. 기존 모델 통신 대기 설정과 프로젝트 자체의 Lean 설정은 별개이며, 이번 변경은 하네스가 Lean 프로세스를 시간으로 강제 종료하던 제한을 제거한다.</p></section><section id="repair-scope"><h2>실제로 어디까지 돌렸나?</h2>
<p class="banner"><b>실제 데이터로 하네스 → Lean 검증 → LLM 피드백 수정은 실행했다.</b><br>
그러나 기존에 설계한 자동 로컬 수리 에이전트를 전체 문제에 연결한 실험은 아니다.
LLM 없는 회복은 별도 스크립트로 수행한 동일 코드 재시도·재선택이다.</p>
<div class="scroll"><table><tr><th>단계</th><th>실행 여부</th><th>이번 결과의 의미</th></tr>
<tr><td>원본 검사 → 모델 후보 → Lean 검사 → 오류 피드백 → 다음 후보 → 선택</td><td>실행</td><td>35행·고유 29문제. 원본 검사를 넘은 17문제에서 실제 대화 응답 51회. 나머지 12개는 후보 생성 전 차단.</td></tr>
<tr><td>오류를 받은 모델이 proof body 수정</td><td>실행</td><td>P1·P2·P8 등. 같은 대화 모델이 오류를 읽고 수정했으며 3응답 예산에 포함된다.</td></tr>
<tr><td>timeout 후보를 코드 변경 없이 다시 검증하고 ranking 적용</td><td>별도 사후 실행</td><td>P15·P19의 세 검증 작업. 추가 LLM 호출 0, proof 편집 0. 기본 하네스에 자동 재시도 정책으로 통합한 것은 아니다.</td></tr>
<tr><td>AST 삭제·변경 구간 rollback·simp?/aesop?/exact?로 자동 proof 수리</td><td>이번 29문제 실행에는 미연결</td><td>효과를 측정했다고 주장할 수 없다. 아래 제안은 다음 비교 실험 대상이다.</td></tr>
<tr><td>계측 wrapper·설치 경로 해석 오류 수정</td><td>실행기 어댑터에서 보정</td><td>분석 중 사람이 개입하듯 코드를 수정한 하네스 수리다. 자율 수리 에이전트의 성공 횟수로 세지 않는다.</td></tr>
</table></div><p>따라서 ‘수리 성공률’ 하나로 합치면 안 된다. <b>증명 수정 성공, 검증 재시도 회복, 실행기 보정, 최종 점수 개선</b>은 각각 별도 결과다.</p></section>
<section id="timeout-explained"><h2>Timeout은 정확히 무엇인가?</h2>
<p>이번 로그의 <code>kind: timeout</code>은 <b>Lean을 실행한 명령 하나가 벽시계 시간 180초 안에 종료되지 않아 하네스가 프로세스 그룹을 종료했다</b>는 뜻이다. 종료 처리 때문에 기록은 180.1초처럼 조금 길 수 있다. 모델 응답 대기 timeout이나 Lean 내부 heartbeat 한도 초과를 뜻하지 않는다.</p>
<p>후보 하나의 주 버전 검증은 <code>check → measure-1 → measure-2 → measure-3</code> 순서다. 각 명령에 180초가 따로 적용된다. 첫 단계는 계측 옵션을 넣지 않은 일반 컴파일, 뒤 세 단계는 새 프로세스의 heartbeat·공리 계측이다. 하나라도 실패하면 그 후보는 해당 실행에서 유효 처리되지 않는다.</p>
<p>여기서는 <b>파일 전체를 컴파일</b>하므로 timeout에는 import 로딩과 주변 선언 처리도 포함된다. 반면 점수의 heartbeat는 대상 선언을 감싼 계측 구간의 값이다. 따라서 ‘180초 초과’와 ‘대상 증명이 논리적으로 틀림’ 또는 ‘대상 heartbeat가 큼’은 같은 판정이 아니다.</p>
<div class="scroll"><table><tr><th>실제 대상</th><th>처음 실행에서 멈춘 위치</th><th>동일 코드 사후 재시도</th></tr>''']
    for n, stage, retry in [(15, 'steps/002', 'steps-002'), (19, 'steps/002', 'steps-002'), (19, 'final', 'final')]:
        base = f'runs/live-practice-2026-10-28/{n}'
        before_path = f'{base}/raw-v2/{stage}/' + ('evaluation/result.json' if stage.startswith('steps') else 'result.json')
        after_path = f'{base}/posthoc-timeout-retry/{retry}/result.json'
        before = json.loads((ROOT / before_path).read_text())['environments']['fixed']['runs']
        after = json.loads((ROOT / after_path).read_text())['environments']['fixed']['runs']
        stopped = next(r for r in before if r['timed_out'])
        completed = ', '.join(f'{r["source"].removesuffix(".lean")}: {r["seconds"]:.1f}초' for r in after)
        out.append(f'<tr><td>P{n} / {stage}</td><td>{html.escape(stopped["source"])} · {stopped["seconds"]:.1f}초<br>{evidence(before_path, "최초 기록")}</td><td>일반 컴파일 + 계측 3회 모두 통과<br>{html.escape(completed)}<br>{evidence(after_path, "재시도 기록")}</td></tr>')
    out.append('''</table></div><p>P15 후보2는 일반 컴파일 79.6초, 계측1 66.4초, 계측2 94.2초까지 통과한 뒤 계측3에서 timeout이 났다. 성공한 일부 표본만 골라 점수를 만들지 않고 후보를 미확정으로 두었다.</p>
<p>P19 후보3도 일반 컴파일에서 timeout이 났다. 후보3의 코드는 최종 선택 코드와 바이트 단위로 같으므로, 위의 ‘P19 final’ 재시도가 같은 코드의 회복을 보여준다. 다만 원래 후보3의 실행 기록을 성공으로 덮어쓰지는 않았다. 후보 거절 중 timeout은 3건이며, 최종 재검증 timeout 1건은 별도다.</p>
<p><b>원인을 확정한 것은 아니다.</b> 동일 코드·동일 제한 재시도의 성공은 관측했다. 자원 경합, 캐시 상태, 파일 전체 처리 비용 중 무엇이 어느 정도 원인이었는지를 분리한 실험은 하지 않았다. P18 원본은 timeout 뒤 재시도에서 sorryAx가 확인됐으므로, 재시도가 항상 유효한 증명을 회수하는 것도 아니다.</p></section>
<section id="effective-cases"><h2>어떤 처리가 실제로 유효했나?</h2>
<article><h3>① P15: 좋은 후보를 timeout 때문에 버리지 않기</h3>
<p><b>실행 검증 회복 · 추가 LLM 없음.</b> 기본 실행은 후보2가 마지막 계측에서 timeout이 나 후보1을 유지했다. 같은 후보2를 다시 검사하자 모두 통과했다. proof는 수정하지 않았다.</p>
<p>기본 최종 선택은 633 tokens / 25,695,751 raw HB / <b>43.229점</b>. 재시도한 후보2는 617 tokens / 25,145,557 raw HB / <b>44.546점</b>으로 +1.317점이었다. 원본 기준으로는 805 tokens / 28,027,779 raw HB다. 이번 이득은 새 proof를 만든 데서 나온 것이 아니라 <b>이미 생성된 좋은 후보를 검증 가능하게 만든 것</b>이다.</p></article>
<article><h3>② P19: 증명 개선을 만든 주체와 회수한 주체 구분하기</h3>
<p><b>LLM이 개선 후보 생성 → timeout → LLM 없는 재시도로 회수.</b> 후보1은 중복된 경우 분석을 공유했지만 heartbeat가 증가했다. 후보2에서는 색상이 Fin 2에 속한다는 산술 상황을 이용해 다음 부분을 바꿨다.</p>
<pre>-- 후보1의 일부
have : color (Sym2.mk (A2 i, y)) = 0 ∨ color (Sym2.mk (A2 i, y)) = 1 := by grind
exact this.resolve_right h1

-- 후보2의 같은 부분: 모델이 생성한 변경
omega</pre>
<p>후보2는 최초 일반 컴파일에서 timeout이 났지만, 동일 코드를 재시도하자 통과했다. 기본 선택 후보1의 계측 점수 33.581에 비해 후보2는 <b>53.604점</b>으로 +20.023점이다. 기본 실행의 최종 검증 자체는 실패했으므로, 33.581은 ‘최종 제출 성공 점수’가 아니라 그 전에 얻은 후보1 계측 점수다.</p>
<p>후보2의 538 tokens / 3,858,450 raw HB는 후보1의 570 tokens / 7,560,366 raw HB보다 좋았다. <b>omega로 바꾸는 아이디어를 자동 수리기가 발견한 것은 아니다.</b> 자동화할 수 있다고 실증된 부분은 동일 코드 재시도와 점수에 따른 재선택이다.</p></article>
<article><h3>③ P1·P2: 오류 피드백을 받은 모델의 국소 수정</h3>
<p><b>LLM 증명 수리 · 실제 Lean 통과.</b> P1 후보2는 <code>assumption</code>으로 끝내려 했지만 귀납가설이 아직 필요한 가정에 적용되지 않은 상태였다. 후보3에서 다음 한 줄을 추가했다.</p>
<pre>specialize e1ih He1  -- 후보3에서 추가
specialize e2ih He2
apply Hwfc.eqcongr &lt;;&gt; assumption</pre>
<p>P1은 수리된 후보3이 최종 선택돼 <b>38.363점</b>이었다. P2 후보1은 abs 합동성 적용에 인수가 부족했다. 후보2에서 원래 문맥의 metadata와 type 인수 <code>m ty</code>를 명시해 통과했다.</p>
<pre>-- P2 후보1: 타입 불일치
exact Hwfc.1 σ σ' _ _ (ih Hinv)
-- P2 후보2: 통과
exact Hwfc.1 σ σ' _ _ (ih Hinv) m ty</pre>
<p>P2는 이후 후보3에서 추가 압축돼 최종 <b>41.429점</b>이었다. 이 값 전체를 두 인수 추가의 효과라고 볼 수는 없다. 이 사례들은 ‘오류 종류·goal·로컬 가설 타입을 수리기에 전달하면 좋다’는 근거이며, LLM 없는 타입 기반 수리 성능은 아직 측정하지 않았다.</p></article>
<article><h3>④ P8·P9: 고쳐져도 최종 선택하면 안 되는 후보</h3>
<p>P8에서 마지막 <code>all_goals grind</code>를 제거하자 identity 경우 두 개가 남았다. 모델이 다음 마무리를 추가한 후보2는 통과했다.</p>
<pre>all_goals
  intro s' htr
  exact ⟨s', htr, ParAssoc.id⟩</pre>
<p>그러나 후보2는 원본 276 tokens보다 긴 286 tokens였고, heartbeat 감소가 이를 보상하지 못해 선택되지 않았다. 최종적으로는 다른 후보3(275 tokens)이 선택됐다. P9도 수정된 후보2·3은 통과했지만 종합 점수에서 원본을 이기지 못해 <b>원본 fallback</b>을 유지했다. 수리 통과와 최적 후보 선정은 서로 다른 관문이어야 한다.</p></article>
<article><h3>⑤ P12·P13: 수리보다 좋은 새 전략이 효과적이었던 경우</h3>
<p>P12는 기존 두 등식을 연결해 긴 후반 재구성을 제거한 모델 후보가 <b>73.471점</b>을 얻었다. 후보3의 추가 압축은 <code>Set.mem_image.mp</code> 미정의 오류로 거절됐고, 통과한 후보2를 유지했다. 지정 네 버전 모두 통과했다.</p>
<p>P13은 양수를 곱하는 부등식을 직접 정리로 증명하는 등 모델의 세 번 리팩터링 후 raw HB가 53,964,385→25,777,940으로 줄고 <b>51.643점</b>이 됐다. 이 개선을 ‘자동 tactic 수리의 성과’로 분류하지 않는다. 다만 탐색 결과를 직접 증명으로 고정하는 후속 실험의 근거는 된다.</p></article>''')
    out.append('<details><summary>위 사례의 원시 후보·피드백·선택 근거</summary><ul>')
    for n, raw, step in [(1, 'raw', '003'), (2, 'raw-v2', '002'), (8, 'raw-v2', '002'), (9, 'raw-v2', '003'), (12, 'raw-v2', '003'), (13, 'raw-v2', '003')]:
        out.append('<li>' + evidence(f'runs/live-practice-2026-10-28/{n}/{raw}/steps/{step}/event.json', f'P{n} 후보{int(step)}: 피드백·후보 선택 상태') + '</li>')
    out.append('''</ul></details></section>
<section id="harness-proposals"><h2>하네스에 무엇을 추가하면 좋을까?</h2>
<p>우선순위는 이번에 관측한 실패와 낭비를 줄이는 순서다. <b>아래 정책은 구현 제안</b>이며, 사후 재시도 및 어댑터 보정 외에는 새 자동 수리 성능을 검증한 것이 아니다.</p>
<div class="scroll"><table><tr><th>우선순위 / 추가 기능</th><th>구체적인 동작</th><th>관측 근거와 기대 효과</th></tr>
<tr><td>1. 시간제한 없는 검증 + 실패 종류별 분기</td><td>Lean wall-clock 제한은 null로 두고 완료까지 기다린다. 시간은 관측값으로만 남긴다. compile, 공리 실패, 실행기 실패, 사용자 중단을 별도 경로로 기록한다.</td><td>P15·P19는 임의의 180초 제한이 유효 후보를 놓치게 한 사례다. 재시도 성공은 무제한 실행보다 retry가 낫다는 증거가 아니다. P18의 timeout 뒤 sorryAx 발견도 최초 시간 초과만으로 증명 상태를 판단할 수 없음을 보여준다.</td></tr>
<tr><td>2. 단계가 보이는 평가 기록</td><td>ordinary_compile / measurement_sample / axiom_audit / final_recheck와 표본 번호·wall time·부분 성공을 기록. stderr를 경로·JSON 출력과 분리. 계측만 실패하면 renderer 진단으로 분기.</td><td>P15는 세 번째 계측만 timeout. P2는 원본 일반 컴파일은 성공했으나 wrapper 경계 때문에 계측 실패. ArkLib 4.30은 경고문을 설치 경로에 붙여 읽었다. 같은 ‘Lean 실패’로 처리하면 잘못된 proof 수정으로 이어진다.</td></tr>
<tr><td>3. 원본 입력과 공리 검사 신뢰성 보강</td><td>Lean parser로 선언 경계를 확인하고 명제·주변 문맥을 잠근다. 문자 # 전체 금지 대신 command와 cardinality 구문을 구분. module 모드의 대상 공리 검사를 독립 경로와 대조하며 알 수 없는 결과를 통과 처리하지 않기.</td><td>P3·7은 다음 선언이 섞였고, P10·11은 정상 #D를 거절, P27–29는 일반 정리를 공리로 오탐했다. 이 7건은 후보 수리 이전에 해결할 입력·검사기 문제다. 실제 sorryAx 5건은 계속 격리해야 한다. 검사기 수정으로 7건 모두 풀린다는 주장은 아직 불가하다.</td></tr>
<tr><td>4. proof hash 기반 재사용 + 실패 시 best 유지</td><td>문제·문맥·toolchain·환경·계측 정책까지 같은 검증 결과만 재사용. timeout 결과는 영구 실패 캐시에 넣지 않기. 새 최종 검사가 실패하면 상태를 숨기지 않고, 정책이 요구하는 재검증 후 verified incumbent 또는 원본으로 복귀.</td><td>P19 후보3과 final은 같은 코드인데 각각 timeout. P12 후보3 실패 뒤 후보2 보존, P9·23·25 원본 fallback이 유효했다. 최종 재검증을 생략하는 정책과는 구분해야 한다.</td></tr>
<tr><td>5. 변경 구간 기준 최소 rollback / goal 추적</td><td>AST 구간 하나씩 되돌린 후보를 bounded budget 안에서 검증. 모든 잔여 goal을 확인. 텍스트 참조가 없다는 이유만으로 가설을 삭제하지 않기.</td><td>P5의 field_simp 제거가 뒤 conv 경로를 깨뜨렸고 P23 simp 병합은 goal 흐름을 바꿨다. P8에서는 두 goal이 남았고, P9에서는 이름 없는 rfl 사실이 grind에 필요했다. 오류 줄만 수리하는 방식의 한계다. 자동 rollback 효과는 미측정.</td></tr>
<tr><td>6. 타입 정보를 이용한 작은 탐색 → 명시적 proof → 계측</td><td>가설 적용·필수 인수 보충, exact?/simp?/aesop? 등의 제한된 탐색을 별도 후보로 생성. 제안을 명시적 proof로 고정해 fresh 검증·점수 비교. 못 이기면 폐기.</td><td>P1·P2의 국소 수리, P13의 직접 정리 사용이 근거. P8·P9가 보여주듯 ‘고쳐짐’만으로는 채택 불가. 자동 탐색이 이 사례들을 해결할지는 별도 실험 필요.</td></tr>
<tr><td>7. 비용에 따라 escalation</td><td>위에서 정한 오류 분기와 시도 횟수 소진 여부로 결정. 명제·문맥·best·변경 구간·잔여 goal·실패한 결정적 시도를 포함한 프롬프트 출력. 모호한 ‘상태가 확실함’ 대신 실제 로그 존재와 parser/검증 결과로 조건 정의.</td><td>local search가 실패한 goal이나 P12 같은 구조적 재증명이 필요한 경우를 모델에 전달한다. 이번에는 공용 하네스의 최대 3응답 루프를 썼으며, 새 escalation 정책은 아직 비교하지 않았다.</td></tr>
</table></div>
<h3>다음 비교 실험을 한다면</h3><p>같은 원본·모델 후보 묶음을 고정하고, <b>시간제한 없는 기본 하네스 / 검사기 보정 추가 / 제한된 local proof 수리 추가</b>를 따로 비교하는 순서가 적합하다. 여기서 local 수리의 제한은 후보 시도 횟수이며 Lean 실행 시간제한이 아니다. 후보 생성 능력 차이가 수리 효과로 섞이지 않게 한다. 주요 지표는 최종 검증 가능 문제 수, 같은 문제 집합의 final score, 추가 모델 호출 수, 추가 Lean 검사 수·시간, 명제·공리 변경 거절 수다. 이번 보고서는 과거 180초 설정의 기록과 그 아래에서 수행한 사후 재시도 효과를 제공한다. 새 무제한 기준선은 아직 측정하지 않았다.</p>
</section>''')
    return ''.join(out)
