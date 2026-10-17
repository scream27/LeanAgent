# 검증/수리 설계 참고자료·메모 (W03)

Arena의 검증 기준과 오류 피드백을 이용한 수리 절차를 검토하기 위한 초안입니다. 정리 문서와 발표자료는 추후 커밋으로 추가할 예정입니다.

- 작성: 손지연 · 검증/수리 설계
- 날짜: 2026-10-17
- 상태: 참고자료와 설계 메모. 아래 기준과 비교 실험은 제안 단계이며 구현·검증 결과가 아닙니다.

## 1. 설계 범위

- 검증: Lean 커널의 검사와 함께 원래 명제를 바꾸지 않았는지, `sorry`나 허용되지 않은 공리에 의존하지 않는지 확인합니다.
  - 실행의 종료와 요구한 증명의 완성을 구분합니다.
- 수리:
  - 오류 메시지만 모델에 전달할지, 남은 목표와 가정까지 전달할지 검토합니다.
  - 실패한 부분만 수정할지, 증명 본문 전체를 재작성하게 할지 검토합니다.

## 2. 단계 초안

| 단계 | 처리 내용 |
| --- | --- |
| 검증 | Lean 커널 검사 결과와 원래 명제·환경 유지 여부, 허용 공리 기준 확인 |
| 진단 | 오류 메시지 확인<br>예: 제출한 항의 타입 ≠ 필요한 타입 |
| 정보 전달 | 현재 목표와 가정<br>실패한 코드와 실제 오류 메시지 |
| 수정 | 실제 코드 → 수정 코드 |
| 재검증 | 수정한 증명이 원래 명제를 해결하는지 다시 실행하고 성공 기준 확인 |

## 3. 기준 초안

| 질문 | 제안 기준 |
| --- | --- |
| 무엇을 성공으로 인정하는가? | 원래 명제·환경 유지<br>Lean 검사 및 허용 공리 검사 통과 |
| 어떤 피드백을 전달하는가? | 실패한 코드<br>실제 오류 메시지<br>오류 위치<br>확보 가능한 현재 목표와 가정 |
| 어디까지 수정하는가? | 명제·가정·주변 정의·의존성은 고정 |
| 언제 재시도·중단하는가? | 최대 3회 수정<br>별도 종료 사유 기록: 같은 후보 반복, 실행 시간 초과, 예산 소진 |
| 무엇을 기록하는가? | 입력 코드, 피드백, 수정 코드, 실행 명령·버전, 결과, 시도 횟수, 시간, 모델 사용량 |

실패 종류:

- 증명 오류
- 환경·의존성 문제
- 시간·예산 초과

허용 공리 목록과 시간·토큰 예산의 구체적인 값은 후속 설계에서 정해야 합니다.

## 4. 참고자료

| 자료 | 링크 | 읽을 부분 | 가져올 설계 아이디어 |
| --- | --- | --- | --- |
| **Lean 공식 문서 — Validating a Lean Proof** | [Lean Reference Manual](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) | 성공 확인, 공리 의존성 검사 부분 | 어떤 결과를 믿을 수 있는가? |
| **APOLLO** | [arXiv 2505.05758](https://arxiv.org/abs/2505.05758) · [본문 (v3)](https://arxiv.org/html/2505.05758v3) | §3 *Our Approach*, Appendix B의 수리 사례 | 실패한 증명의 일부를 어떻게 분리하고 다시 고치는가? |
| **Pantograph / PyPantograph 문서** | [GitHub](https://github.com/stanford-centaur/PyPantograph) · [Introduction](https://github.com/stanford-centaur/PyPantograph/blob/main/doc/intro.md) · [Goals and Tactics](https://github.com/stanford-centaur/PyPantograph/blob/main/doc/goal.ipynb) | *Introduction*, *Goals and Tactics* | 프로그램이 Lean의 목표와 실행 결과를 어떻게 다루는가? |

## 5. 논문 조사 메모

> 전체를 버리고 다시 생성할 것인가, 기존 구조를 보존하고 실패한 부분만 고칠 것인가?

### APOLLO: Automated LLM and Lean Collaboration for Advanced Formal Reasoning

(**A**utomated **P**r**O**of repair via **L**LM and **L**ean c**O**llaboration)

APOLLO는 LLM이 생성한 증명에서 구문 오류와 실패한 부분을 찾아 분리하고, 자동화 도구와 LLM을 이용해 남은 목표를 해결한 뒤 조립한 증명을 재검증하는 절차입니다. 기존 증명 구조를 활용한 부분 수리 설계를 조사하는 데 참고합니다.

## 6. 비교 실험 질문

> **같은 실패한 증명을 고칠 때, 오류 메시지만 주는 것보다 현재 목표와 가정까지 제공하는 것이 도움이 되는가?**

| 방식 | 모델에 제공하는 정보 |
| --- | --- |
| **A: 오류 메시지 기반 수리** | 원래 명제 + 실패한 증명 + Lean 오류 메시지 |
| **B: 목표·가정 포함 수리** | A의 정보 + 실패 지점에서 확보한 현재 목표와 가정 |

- 공통: 같은 실패 코드, 같은 모델, 같은 수정 범위.
- 관찰: 실제 수리 성공 여부, 수정 횟수, 어떤 정보가 사용됐는지.
- 사용량 기록: 입력 길이와 총토큰.

## 7. 실행 기록 항목·명령 메모

```text
- model/version
- prompt
- response
- token/cost
- candidate proof
- Lean result/error
- proof length
- elaboration metric
- toolchain/repo commit
```

아래 명령은 실행·사용량 추출 예시이며 이 저장소에서 실행한 검증 기록이 아닙니다. `Typing.progress`와 출력 파일명은 실제 대상에 맞게 바꿔야 합니다.

```sh
codex exec --json \
  "Refactor only the Typing.progress proof and verify it." \
  > warmup_07.jsonl
```

이후 다음 명령으로 모델 사용량을 추출할 수 있습니다.

```sh
jq 'select(.type == "turn.completed") | .usage' warmup_07.jsonl
```
