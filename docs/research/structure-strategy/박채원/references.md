# 구조·전략 설계 참고 자료 (W03)

에이전트의 최소 실행 구조(단계, 단계별 입출력, 담당, 반복과 멈춤, 후보 선택, 기록)를 설계하기 위해 읽을 자료 목록입니다. 정리 문서는 별도로 올릴 예정입니다.

- 작성: 박채원 · 구조/전략 설계
- 날짜: 2026-10-15

## 1. 논문

| 우선순위 | 논문 | 공개·학회 | 링크 | 읽을 부분 | 설계와 연결되는 질문 |
| --- | --- | --- | --- | --- | --- |
| 필수 | Lean Refactor: Multi-Objective Controllable Proof Optimization via Agentic Strategy Search | 2026-05 arXiv · ICML 2026 | [arXiv 2605.20244](https://arxiv.org/abs/2605.20244) · [PDF](https://arxiv.org/pdf/2605.20244) | 3.1 전략 은행, 3.2 검색, 3.3 에이전트 루프(Algorithm 1), Table 1·3, Appendix I.4·L | 단계 구성, 목표(길이·시간·버전)별 전략 검색, 반복·멈춤 조건, heartbeat 측정 방법 |
| 권장 | ProofOptimizer: Training Language Models to Simplify Proofs without Human Demonstrations | 2025-10 arXiv · ICLR 2026 | [arXiv 2510.15700](https://arxiv.org/abs/2510.15700) | 2장, 3.2 추론 기법, 4.3 반복 축약, 5.2·5.2.1 실행 시간과 heartbeat | 규칙 전처리(린터), 반복 축약 루프, 수리 vs 다시 뽑기, 길이 vs heartbeat 기준 |
| 선택 | ImProver: Agent-Based Automated Proof Optimization | 2024-10 arXiv · ICLR 2025 | [arXiv 2410.04753](https://arxiv.org/abs/2410.04753) | 3.1 (Chain-of-States, 출력 형식, 샘플링, 검색) | 프롬프트 구성, 후보 비교 규칙 |
| 선택 | APOLLO: Automated LLM and Lean Collaboration for Advanced Formal Reasoning | 2025-05 arXiv · NeurIPS 2025 | [arXiv 2505.05758](https://arxiv.org/abs/2505.05758) | 3장, Algorithm 1 | 오류 위치 기반 국소 수리 |
| 참고 | LeanDojo: Theorem Proving with Retrieval-Augmented Language Models | 2023-06 arXiv · NeurIPS 2023 | [arXiv 2306.15626](https://arxiv.org/abs/2306.15626) | 4장, 5장 (ReProver) | 정리(premise) 검색 |
| 참고 | Kimina Lean Server | 2025-04 arXiv | [arXiv 2504.21230](https://arxiv.org/abs/2504.21230) | 서버 구조, 성능 비교 | 대량 검증 처리 |

## 2. Lean 상호작용 도구

| 도구 | 링크 | 용도 |
| --- | --- | --- |
| lean-lsp-mcp | [소개 페이지](https://glama.ai/mcp/servers/oOo0oOo/lean-lsp-mcp) | Claude Code 등 에이전트가 goal·오류 확인, Mathlib 검색, tactic 시도 |
| LeanInteract | [GitHub](https://github.com/augustepoiroux/LeanInteract) | Python에서 Lean REPL 호출 |
| Kimina Lean Server | [arXiv 2504.21230](https://arxiv.org/abs/2504.21230) | REPL 여러 개로 대량 검증 |

## 3. Lean 기초 학습

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/) — 5장 Tactics
- [Lean 4 tactic 치트시트 (Floris van Doorn)](https://florisvandoorn.com/files/lean-tactics.pdf)
- [Natural Number Game](https://adam.math.hhu.de)
