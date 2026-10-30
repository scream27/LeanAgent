# 공용 하네스 × 검증·수리 에이전트 — P1·P2

2026-10-27 · 고정 후보 6개 · 별도 모델 API 호출 0회 · 공식 평가 아님

공용 하네스 revision: `ba593fc4357ee5c429b8f28f1aac512d05bb4355`.
실제 패키지는 `src/lean_agent`이다. 핵심 코드는 수정하지 않았다.

## 실제 결과

- 최초 후보 4/6 통과. 실패를 만들기 위한 mutation은 사용하지 않았다.
- 로컬 시도 결과: {'invalid': 10, 'no_supported_suggestion': 6, 'valid': 2}.
- 수리·정리 전후 평균 선택 점수: **63.873 → 63.873**.
- 두 최종 후보 모두 전체 원문 문맥에서 재검증했다. 지정 환경은 각각 Lean 4.26.0 하나이다.
- `refactoring_results.json`에는 모든 후보·측정·선택·로그 경로를, `p1.response.json`과 `p2.response.json`에는 공용 하네스가 받는 정확한 `{"proof":"by ..."}`를 넣었다.
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

## JSON 진단 후속 실험

위치 없는 plain-text 제안 2건을 Lean --json으로 다시 수집했다. 두 명시적 증명이 전체 재검증에 통과했지만 최종 선택을 이기지는 못했다. 이는 solver 성공률 개선이 아니라 제안 수집 손실을 복구한 결과다. 첫 고정 18회 처리와 분리한 탐색적 후속 실험이며 query_upgrade.py에 재현 코드가 있다.

개발 중 부가 기록을 이미 봉인된 raw 디렉터리에 추가하려던 저장 충돌은 부가 기록을 밖으로 옮겨 해결했다. JSON 후속 실험에서 반복된 동일 tactic 문자열을 유일하다고 가정한 첫 probe는 위치 assertion에서 중단되었고, 실제 source offset으로 교체하도록 고쳤다. 해당 pilot 로그는 json-query-followup-position-pilot에 보존했으며 최종 실험 횟수에 섞지 않았다.
