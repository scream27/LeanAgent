# Warm-up 모의 실행 결과

점수는 공식 제출 점수가 아닌 로컬 모의 점수입니다. 원본의 모든 지정 버전 통과 점수는 33.3333입니다.
P1: 구조 유지 간소화 · P2: 구조 개선 · P3: 비용 축소. 모델에 escalation 요청을 보내지 않았습니다.

| 문제 | 선택 | 원본 점수 | 선택 점수 | 판정 |
|---|---|---:|---:|---|
| 1 | P1/raw | 33.3333 | 35.4116 | 성공(개선) |
| 2 | P3/raw | 33.3333 | 33.7243 | 성공(개선) |
| 3 | P1/raw | 33.3333 | 37.3276 | 성공(개선) |
| 4 | P3/raw | 33.3333 | 33.7175 | 성공(개선) |
| 5 | P1/raw | 33.3333 | 33.3981 | 성공(개선) |
| 6 | P3/raw | 33.3333 | 33.6780 | 성공(개선) |
| 7 | P3/raw | 33.3333 | 33.3769 | 성공(개선) |
| 8 | original | 33.3333 | 33.3333 | 원본 보존(사용자 지정) |
| 9 | P2/raw | 33.3333 | 43.5486 | 성공(개선) |
| 10 | P2/raw | 33.3333 | 33.4026 | 성공(개선) |
| 11 | P2/raw | 33.3333 | 34.9025 | 성공(개선) |
| 12 | P1/raw | 33.3333 | 33.4513 | 성공(개선) |
| 13 | P2/extraction | 33.3333 | 41.2370 | 성공(개선) |
| 14 | P3/raw | 33.3333 | 34.2185 | 성공(개선) |
| 15 | P2/raw | 33.3333 | 34.2961 | 성공(개선) |

| 프롬프트 | 최초 개선 | 최초 악화 | 최초 invalid | 원본 유지 | 미완료 | 처리 후 개선 |
|---|---:|---:|---:|---:|---:|---:|
| P1 | 11 | 1 | 2 | 1 | 0 | 11 |
| P2 | 8 | 1 | 3 | 3 | 0 | 8 |
| P3 | 11 | 1 | 2 | 1 | 0 | 11 |

단순 프롬프트 결과와 로컬 수리·최적화 이후 결과를 아래에서 구분합니다. invalid는 컴파일 실패이며, worse는 검증은 통과했지만 점수가 낮아진 경우입니다.

o200k_base token counts; synchronous Lean declaration heartbeats. Not official Arena scores.
Rows with missing environments/versions are unresolved, never silently treated as proof failures.
Candidates were frozen before feedback; model escalation prompts are printed only.

| ID | Prompt | Raw outcome | Raw score | Best local score | Final | Policy |
|---|---|---|---:|---:|---|---|
| 1 | P1 | improved | 35.4116 | 35.4116 | improved | SELECT_BEST |
| 1 | P2 | invalid | — | — | original_fallback | EMIT_LLM_PROMPT |
| 1 | P3 | improved | 34.1233 | 34.1233 | improved | SELECT_BEST |
| 2 | P1 | improved | 33.3739 | 33.3739 | improved | SELECT_BEST |
| 2 | P2 | invalid | — | — | original_fallback | EMIT_LLM_PROMPT |
| 2 | P3 | improved | 33.7243 | 33.7243 | improved | SELECT_BEST |
| 3 | P1 | improved | 37.3276 | 37.3276 | improved | SELECT_BEST |
| 3 | P2 | improved | 33.6805 | 33.6805 | improved | SELECT_BEST |
| 3 | P3 | improved | 33.7463 | 33.7463 | improved | SELECT_BEST |
| 4 | P1 | worse | 33.3307 | 33.3307 | original_fallback | EMIT_LLM_PROMPT |
| 4 | P2 | improved | 33.4805 | 33.4805 | improved | SELECT_BEST |
| 4 | P3 | improved | 33.7175 | 33.7175 | improved | SELECT_BEST |
| 5 | P1 | improved | 33.3981 | 33.3981 | improved | SELECT_BEST |
| 5 | P2 | worse | 33.2969 | 33.2969 | original_fallback | EMIT_LLM_PROMPT |
| 5 | P3 | invalid | — | — | original_fallback | EMIT_LLM_PROMPT |
| 6 | P1 | improved | 33.5315 | 33.5315 | improved | SELECT_BEST |
| 6 | P2 | unchanged | 33.3333 | 33.3333 | original_fallback | EMIT_LLM_PROMPT |
| 6 | P3 | improved | 33.6780 | 33.6780 | improved | SELECT_BEST |
| 7 | P1 | improved | 33.3456 | 33.3456 | improved | SELECT_BEST |
| 7 | P2 | unchanged | 33.3333 | 33.3333 | original_fallback | EMIT_LLM_PROMPT |
| 7 | P3 | improved | 33.3769 | 33.3769 | improved | SELECT_BEST |
| 8 | P1 | unchanged_user_excluded | 33.3333 | 33.3333 | original_fallback | USER_EXCLUDED |
| 8 | P2 | unchanged_user_excluded | 33.3333 | 33.3333 | original_fallback | USER_EXCLUDED |
| 8 | P3 | unchanged_user_excluded | 33.3333 | 33.3333 | original_fallback | USER_EXCLUDED |
| 9 | P1 | invalid | — | 33.0497 | original_fallback | EMIT_LLM_PROMPT |
| 9 | P2 | improved | 43.5486 | 43.5486 | improved | SELECT_BEST |
| 9 | P3 | invalid | — | — | original_fallback | EMIT_LLM_PROMPT |
| 10 | P1 | improved | 33.4018 | 33.4018 | improved | SELECT_BEST |
| 10 | P2 | improved | 33.4026 | 33.4026 | improved | SELECT_BEST |
| 10 | P3 | improved | 33.3369 | 33.3369 | improved | SELECT_BEST |
| 11 | P1 | invalid | — | — | original_fallback | EMIT_LLM_PROMPT |
| 11 | P2 | improved | 34.9025 | 34.9025 | improved | SELECT_BEST |
| 11 | P3 | improved | 33.4056 | 33.4056 | improved | SELECT_BEST |
| 12 | P1 | improved | 33.4513 | 33.4513 | improved | SELECT_BEST |
| 12 | P2 | invalid | — | — | original_fallback | EMIT_LLM_PROMPT |
| 12 | P3 | improved | 33.3799 | 33.3799 | improved | SELECT_BEST |
| 13 | P1 | improved | 33.7444 | 34.9187 | improved | SELECT_BEST |
| 13 | P2 | improved | 40.0603 | 41.2370 | improved | SELECT_BEST |
| 13 | P3 | improved | 35.7793 | 36.9559 | improved | SELECT_BEST |
| 14 | P1 | improved | 33.7687 | 33.7687 | improved | SELECT_BEST |
| 14 | P2 | improved | 33.9156 | 33.9156 | improved | SELECT_BEST |
| 14 | P3 | improved | 34.2185 | 34.2185 | improved | SELECT_BEST |
| 15 | P1 | improved | 33.5410 | 33.5410 | improved | SELECT_BEST |
| 15 | P2 | improved | 34.2961 | 34.2961 | improved | SELECT_BEST |
| 15 | P3 | worse | 33.3203 | 33.3203 | original_fallback | EMIT_LLM_PROMPT |

공개 기준값과 로컬 원본 계측의 비교입니다. 공식 길이를 로컬 점수의 분모로 혼합하지 않습니다.

| 문제 | 공개 길이 | 로컬 토큰 | 공개 heartbeat | 로컬 heartbeat |
|---|---:|---:|---:|---:|
| 1 | 313 | 692 | 5175 | 5174.3580 |
| 2 | 222 | 509 | 2696 | 2697.7580 |
| 3 | 224 | 488 | 4251 | 4253.0270 |
| 4 | 851 | 2427 | 11947 | 11946.2000 |
| 5 | 1372 | 2588 | 26970 | 26974.5730 |
| 6 | 1217 | 2253 | 42225 | 42182.9910 |
| 7 | 408 | 741 | 59830 | 59806.6420 |
| 8 | 407 | 827 | 1383 | 1382.1810 |
| 9 | 251 | 505 | 3858 | 3856.5740 |
| 10 | 1463 | 4015 | 15645 | 15780.9920 |
| 11 | 1906 | 3534 | 45273 | 45504.2550 |
| 12 | 1353 | 3466 | 9198 | 9282.2540 |
| 13 | 1769 | 2729 | 111476 | 141079.6490 |
| 14 | 1754 | 3422 | 134499 | 120478.0180 |
| 15 | 4085 | 5811 | 14130 | 17952.4620 |

출력한 escalation 프롬프트: 12개. 실제 모델 호출: 0회.

- [01번 / P2](policy/01/P2/prompt.txt)
- [02번 / P2](policy/02/P2/prompt.txt)
- [04번 / P1](policy/04/P1/prompt.txt)
- [05번 / P2](policy/05/P2/prompt.txt)
- [05번 / P3](policy/05/P3/prompt.txt)
- [06번 / P2](policy/06/P2/prompt.txt)
- [07번 / P2](policy/07/P2/prompt.txt)
- [09번 / P1](policy/09/P1/prompt.txt)
- [09번 / P3](policy/09/P3/prompt.txt)
- [11번 / P1](policy/11/P1/prompt.txt)
- [12번 / P2](policy/12/P2/prompt.txt)
- [15번 / P3](policy/15/P3/prompt.txt)

재현 방법·계측 범위·검증기 한계는 [README](README.md), 실제 선택 proof body는 [selected.json](selected.json), 전체 수치는 [results.csv](results.csv)에 있습니다.
실제 escalation 프롬프트는 policy/문제번호/프롬프트이름/prompt.txt에 저장합니다. 호출 권한과 예산 승인을 뜻하지 않는 preview입니다.
이 실험은 같은 대화 문맥에서 생성한 단일 후보 실험이므로 프롬프트의 일반적인 우열을 입증하지 않습니다. 1·2번은 사전 노출이 있습니다.

최종 선택: 14문제 개선, 1문제 원본 유지. 선택 점수 평균은 35.2683입니다. 검증 누락 여부는 [audit.json](audit.json)을 확인하세요.

관찰에서 얻은 설계상 결론:

- 5번: 같은 문제에서 P1 개선, P2 악화, P3 컴파일 실패가 자연스럽게 발생했다. 검증 통과와 점수 개선을 구분해야 한다.
- 9번 P1: 첫 오류 줄의 `exact?` 탐색에서 명시적 `exact ChoiceBisim.choice h`를 추출했다. 같은 수정 body가 세 버전을 통과했지만 원본보다 점수가 낮아 fallback했다. “수리 성공”은 “선택 성공”이 아니다.
- 13번: `simp?`의 제안을 명시적으로 추출한 후보가 최초 후보보다 높은 점수를 얻었다. LLM 없이도 유효한 최적화 후보를 만들 수 있었다.
- 15번 P3: 유효하지만 점수가 낮은 후보를 버리고 원본을 유지하는 분기가 실제로 실행됐다. 최종 문제별 선택에서는 더 나은 다른 프롬프트의 후보를 사용한다.
- 이 결과만으로 신뢰 가능한 tactic-state localization, 악의적인 문맥 변경 방어, 모델을 호출한 뒤의 재수리 루프까지 검증했다고 주장하지 않는다. 해당 기능은 이번 실험의 범위 밖이며 escalation은 body 단위 프롬프트 출력에서 끝냈다.
