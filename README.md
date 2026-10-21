# LeanAgent — Lean Refactor Arena

**Lean 증명을 검증하고 개선하는 리팩터링 에이전트를 만듭니다.**

[가짜연구소 LeanAgent](https://github.com/Pseudo-Lab/LeanAgent)의
[Lean Refactor Arena](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena) 참여 저장소입니다.
문제와 원본 증명을 입력받아 개선 후보를 생성하고, Lean의 검증 피드백으로 수정과 평가를 반복한 뒤
최종 제출 후보를 선택하는 실행 흐름을 개발합니다.

[진행 중인 PR](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/pulls) ·
[개발 브랜치](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/branches) ·
[Warm-up 연구 기록](https://github.com/Pseudo-Lab/LeanAgent/blob/main/docs/research/refactoring/warmup/README.md)

## 목표

원래 명제와 필요한 문맥을 유지하면서 증명 길이와 검증 비용을 줄이고, 지정된 Lean 버전에서
같은 후보가 동작하는지 확인합니다. 짧은 증명이 항상 적은 비용으로 검증되는 것은 아니므로
여러 지표를 함께 비교합니다.

| 확인할 항목 | 의미 |
| --- | --- |
| 증명 정확성 | 원래 명제를 보존하고 Lean 컴파일·공리 검사를 통과하는가 |
| 증명 길이 | 증명 소스의 토큰 수가 원본보다 줄었는가 |
| 검증 비용 | 동일 환경에서 측정한 Lean heartbeat가 줄었는가 |
| 버전 호환성 | 같은 후보가 문제에 지정된 Lean 버전과 의존성에서 검증되는가 |
| 재현성 | 후보 코드, 실행 환경, 검증 로그와 선택 근거를 다시 확인할 수 있는가 |

증명 소스의 토큰 수와 모델 API의 사용 토큰·비용은 별도로 기록합니다.
로컬 측정값과 후보 선택 점수는 공식 Arena 평가 결과와 구분하며,
대회 규칙과 제출 요건은 [공식 Arena](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena)를 기준으로 확인합니다.

## 개발 범위

| 영역 | 주요 작업 |
| --- | --- |
| 문제·실행 환경 | 원본 증명과 문맥 준비, Lean 버전·라이브러리 commit·의존성 고정 |
| 에이전트·리팩터링 전략 | 모델 API 연결, 후보 생성, 증명 구조와 tactic 선택 전략 탐색 |
| 검증·수리 | 컴파일 오류와 검증 결과 전달, 수정 범위·재시도·종료 조건 설계 |
| 평가·후보 선택 | 원본과 후보의 지표 측정, 중간 기록, 최종 재검증과 후보 선택 |
| 실험 분석·제출 | 문제별 결과 비교, 스코어보드, 제출 산출물과 실행 근거 정리 |

전체적으로 연결할 실행 흐름은 다음과 같습니다.

```text
문제와 지정 환경 준비 → 원본 검증·기준값 측정
  → 후보 생성 → 검증·측정·기록 → 피드백을 반영한 수정·추가 개선 ↺
  → 탐색 종료 → 최종 후보 재검증·선택 → 제출 산출물 준비
```

에이전트는 후보 생성과 개선 전략을 담당하고, 평가 하네스는 후보를 검증·측정·기록합니다.
후보 코드와 부모 후보, 실행 환경, 오류와 측정값, 선택 사유를 연결해 남기는 것을 목표로 합니다.

## 현재 개발 현황

**2026-10-21 기준**, `main`은 프로젝트 안내와 라이선스를 제공하며 구현과 연구 자료는 아래 브랜치에서 검토 중입니다.
아래 링크는 아직 병합되지 않은 브랜치의 자료로 연결됩니다. PR 병합 시 상태와 문서 링크를 함께 갱신합니다.

| 작업 | 포함된 내용 | 브랜치·PR | 상태 |
| --- | --- | --- | --- |
| 구조·전략 설계 | 선행 연구, 에이전트 단계·입출력·반복·후보 선택을 위한 참고자료 | [docs/week3-structure-references](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/tree/docs/week3-structure-references) · [#1](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/pull/1) | PR 열림 · 참고자료 단계 |
| 검증·수리 설계 | 성공 기준, 오류 피드백, 수정 범위, 재시도와 기록 항목 | [docs/week3-verification-repair-references](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/tree/docs/week3-verification-repair-references) · [#2](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/pull/2) | PR 열림 · 설계 메모 단계 |
| 평가 하네스·환경 고정 | 후보 검증·측정·선택 코드, 문제별 환경 고정 제안과 로컬 파일럿 | [proposal/problem-environment-lock](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/tree/proposal/problem-environment-lock) · [#3](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/pull/3) | PR 열림 · 환경 고정은 가안 |
| 팀 스코어보드 | 문제별 토큰·heartbeat·호환성 상태와 결과 비교 화면 | [feat/team-score-dashboard](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/tree/feat/team-score-dashboard) | 브랜치에 구현 · PR 없음 |

평가 하네스는 환경 고정 제안과 스코어보드 브랜치에 공통으로 포함되어 있습니다.
모델 API와 실제 생성 에이전트의 통합, Linux 실행 격리, 공식 worker와의 평가 동등성은 후속 검증 대상입니다.
현재 자료가 전체 에이전트의 구현 완료나 공식 제출 완료를 뜻하지는 않습니다.

### 확인된 검증 기록

다음은 개발 브랜치에 보존된 실행 기록입니다. README 작성 시 새로 실행한 결과는 아닙니다.

- **평가 하네스:** 2026-10-18 기록에서 실제 Lean 통합 테스트 4개를 포함해 30개 테스트 통과,
  공개 Warm-up 15개 원본의 토큰 수 15/15 일치.
  [검증 기록](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/blob/proposal/problem-environment-lock/docs/validation.md)
- **환경 고정 파일럿:** Strata·PutnamBench 두 문제의 네 환경에서 컴파일 24회 수행.
  정상 경로 20회 성공, 의도적으로 잘못 만든 후보 4회 실패.
  macOS 로컬 검증이며 공식 점수나 Linux worker 동등성을 확인한 결과는 아닙니다.
  [환경 설계와 파일럿 범위](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/blob/proposal/problem-environment-lock/docs/environment-architecture.md)

## 자료와 실행 안내

1. **처음 참여한다면:** [LeanAgent 프로젝트 소개](https://github.com/Pseudo-Lab/LeanAgent)와
   [Warm-up 문제별 연구 기록](https://github.com/Pseudo-Lab/LeanAgent/blob/main/docs/research/refactoring/warmup/README.md)을 확인합니다.
2. **설계를 검토한다면:** [구조·전략 자료 PR #1](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/pull/1),
   [검증·수리 자료 PR #2](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/pull/2),
   [환경 고정 제안 PR #3](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/pull/3)에서 변경 내용과 논의를 확인합니다.
3. **평가 코드를 실행한다면:** 현재 `main`에는 실행 코드가 없으므로 해당 개발 브랜치의 문서를 사용합니다.
   [평가 하네스 사용법](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/blob/feat/team-score-dashboard/docs/evaluation.md)에서
   Python·Lean 준비, 예제 실행, API 연결과 최종 선택 절차를 확인할 수 있습니다.
   이 사용법은 `feat/team-score-dashboard` 브랜치 기준입니다.
4. **결과 화면을 확인한다면:** [스코어보드 실행 안내](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/blob/feat/team-score-dashboard/dashboard/README.md)를 따릅니다.
   현재 화면은 저장된 JSON을 읽는 정적 대시보드이며 자동 수집 기능은 포함하지 않습니다.

## 함께 작업하기

- 작업 브랜치에서 변경하고 PR에 목적, 변경 범위와 검증 결과를 남깁니다.
- 실험 결과에는 문제·후보·Lean 버전·의존성·실행 명령·로그를 연결하고, 실패와 미검증 상태도 기록합니다.
- 설계 제안, 구현된 기능, 실제 검증 결과를 구분해 문서에 표시합니다.
- 실행 환경과 사용법은 해당 모듈 문서에서 관리하고, README에는 주요 진입점과 개발 상태를 유지합니다.

## 관련 저장소와 라이선스

- [Pseudo-Lab/LeanAgent](https://github.com/Pseudo-Lab/LeanAgent): 시즌 목표, 학습·발표 자료와 Warm-up 연구 기록.
- [Pseudo-Lab/LeanAgent-LeanRefactorArena](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena): 대회용 리팩터링 에이전트, 평가·실행 환경과 제출 준비.

이 저장소는 [MIT License](LICENSE)를 따릅니다. 외부 benchmark와 라이브러리는 각 원출처의 라이선스를 확인합니다.
