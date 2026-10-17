# Verifier-guided Agent

Lean 도구 연결과 검증 피드백을 이용한 증명 생성·오류 분석·반복 수정·최적화를 조사하는 자료 공유 폴더입니다.

## 담당자

정소미 · 박성호

## 시작할 자료

- [전체 논문 목록](../papers.md)에서 `Verifier-guided Agent` 태그를 확인합니다.
- Lean Refactor, APOLLO, Learning to Repair Lean Proofs from Compiler Feedback.
- 도구·구현 참고: Numina-Lean-Agent, Pantograph, LeanDojo, LeanExplore.
- 확장 참고: LeanArchitect, ProofBridge, Awakening the Sleeping Agent.

## 공유 자료

| 작성자 | 주제 | 자료 링크 | 공유일 |
| --- | --- | --- | --- |
| 남성우 | Arena 검증·수리 harness: 프레임워크·문헌 조사 및 구현 초안 | [검증·수리 설계 계획](./arena-verification-repair-plan-2026-10-13.md) | 2026-10-13 |
| 남성우 | 합의한 Python·Lean 방향 및 두 논문 추가 검토 | [읽기 쉬운 전체 계획](./arena-harness-plan-readable.md) · [추가 검토 보고서](./leanflow-copilot-review-2026-10-13.md) | 2026-10-13 |
| 남성우 | 최고 combined 후보 선택·원본 fallback 및 검증 데이터 | [파이프라인 검증 데이터 설계](./arena-pipeline-validation-data.md) | 2026-10-13 |
| 남성우 | 자동화 수리의 HB 비용과 후속 모델 최적화 | [자동화 수리 후 최적화](./automation-repair-and-optimization.md) | 2026-10-13 |
| 남성우 | Escalation 조건·프롬프트 출력 및 Gemini 데이터 제작 | [정책과 recipe](./escalation-policy-and-data-recipe.md) · [Gemini 전달 요청서](./gemini-validation-data-request.md) · [정책 코드](./escalation_policy.py) | 2026-10-14 |
| 남성우 | Warm-up 15문제·3개 프롬프트 실제 실행 및 지정 버전 검증 | [실험 결과](./experiments/warmup-2026-10-15/REPORT.md) · [실행 방법과 한계](./experiments/warmup-2026-10-15/README.md) · [선택 proof](./experiments/warmup-2026-10-15/selected.json) | 2026-10-17 |

자료를 이 폴더에 자유로운 형식으로 작성하고, 위 표에 링크를 추가합니다.
