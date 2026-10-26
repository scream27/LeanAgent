# 첫 하네스: 팀 공통 실행 기준점

단일 모델이 증명 본문 하나를 제안하면 하네스가 검증·측정하고 다음 요청에 피드백을 전달합니다.
첫 버전은 실행·후보 선택·기록 재생의 기준점입니다. 기본 예제는 고정 응답을 사용하므로
모델의 문제 해결 성능이나 공식 대회 점수를 측정하지 않습니다.

원본은 [첫 하네스 커밋 a4b4662](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/tree/a4b46622aaea36a9d4470a01ec048613b45fb08a/experiments/first-harness-jwkweon)입니다.
평가·선택 규칙을 유지하고 패키지 경로, 실행 진입점, 보관 코드의 실행 방법을 정리했습니다.
후속 프롬프트·피드백 실험과 그 결과물은 원래 실험 브랜치에서 관리합니다.

## 설치와 실행

Python 3.10 이상을 사용하는 프로젝트 환경에서 저장소 루트를 기준으로 실행합니다.
하네스 실행 코드의 외부 Python 의존성은 없습니다.
스모크 실행에는 미리 설치된 `leanprover/lean4:v4.26.0`과 PATH의 `lean`이 필요합니다.

```sh
python -m pip install -e .
python -m lean_agent run --config configs/smoke.json --output runs/first-harness/trial-01
python -m lean_agent replay runs/first-harness/trial-01
```

설치 후 `lean-agent` 명령도 같은 기능을 제공합니다. 설정 파일의 상대 경로는 설정 파일 위치를
기준으로 해석하고, `--output`은 현재 작업 폴더를 기준으로 해석합니다. 독립 반복에는 새 출력
폴더를 사용합니다. 기존 실행 폴더는 덮어쓰지 않습니다.

스모크 입력은 `n + 0 = n`이며, 고정 응답은 컴파일 실패 → 유효한 개선 → `by rfl` 순서입니다.
예산 3회를 사용하고 최종 `summary.json`의 `status: completed`, `final_valid: true`,
선택 증명 `by rfl`과 replay의 `record_replay_passed: true`를 확인합니다.
이 예제의 모델 API 호출과 비용은 0입니다. 실제 heartbeat 표본은 반복 간 달라질 수 있습니다.

## 실행 흐름과 구성

```text
코드·입력·설정 스냅샷 → 원본 검증·기준값 측정
  → 후보 요청 → 응답 해석 → Lean 검증·측정 → 최선 후보 갱신 ↺
  → 최선 후보 재검증 → 결과·해시 저장
```

| 위치 | 역할 |
| --- | --- |
| `src/lean_agent/harness.py` | 실행 루프, 문맥·상태, 종료·선택 규칙, 스냅샷·replay |
| `src/lean_agent/models.py` | 고정 응답과 OpenRouter 연결, 사용량·비용 해석 |
| `src/lean_agent/evaluator/` | 명제·공리 검사, Lean 컴파일, 토큰·heartbeat 측정 |
| `configs/` | 스모크 설정과 OpenRouter 설정 예제 |
| `examples/first-harness/` | 작은 입력 문제, 컴파일 문맥, 프롬프트, 고정 응답 |
| `tests/test_harness.py` | 상태 전이·실패 처리·기록 무결성·패키지 replay 검사 |

후보는 원래 문맥에서 한 번 컴파일하고, 통과하면 새 Lean 프로세스에서 3회 계측합니다.
선택 기준은 `0.5 × (후보 토큰 / 원본 토큰 + 후보 raw heartbeat / 원본 raw heartbeat)`이며
heartbeat는 표본 중앙값을 사용합니다. 실제 비교에는 같은 비율을 나타내는 정수 분자를 사용하고,
동점이면 토큰 수와 선언 SHA256으로 결정합니다. 유효한 원본이 기본 후보이고 무효 후보는 선택하지 않습니다.
증명 토큰은 모델 API의 과금 토큰과 구분합니다.

## 기록과 재생

각 실행은 `input/`, `code/`, `baseline/`, `steps/`, `selected.lean`, `final/`,
`manifest.json`, `summary.json`, `artifacts.json`을 남깁니다. 코드·입력·컴파일러 식별 정보와
실제 요청·응답·후보·원문 로그·측정값을 보존하며, Git checkout 정보는 확인 가능한 경우 기록합니다.
정확한 실행 코드와 입력은 Git 유무와 관계없이 복사하고 해시를 기록합니다.

코드가 바뀌어 현재 패키지로 replay할 수 없으면 해당 실행에 보관한 코드를 사용합니다.

```sh
python -B runs/first-harness/trial-01/code/replay.py replay runs/first-harness/trial-01
```

replay는 저장된 관측으로 요청·상태 전이·종료 조건·최종 선택을 다시 계산합니다.
모델이나 Lean을 재호출하지 않으며 새 증명 검증을 대신하지 않습니다.
이전 실험 브랜치에서 만든 실행 기록은 당시 보관된 코드를 사용합니다.
실행 결과 폴더는 Git에 추가하지 않고 필요한 요약과 실행 조건을 PR에 기록합니다.

## 테스트와 지원 범위

```sh
python -m unittest discover -s tests -p 'test_harness.py' -v
```

이 테스트와 Harness CI는 Lean 설치·네트워크·모델 API 없이 실행합니다.
실제 Lean 스모크와 replay는 위의 실행 명령으로 별도 확인합니다.

현재 기본 실행기는 외부 라이브러리 의존성이 없는 Lean 프로젝트와 단일 환경을 지원합니다.
OpenRouter 설정 예제는 정확한 모델 ID·provider를 지정한 뒤 사용하며,
인증은 `OPENROUTER_API_KEY` 환경 변수로 받습니다. `.env`를 자동 로드하지 않습니다.
인증 헤더는 기록하거나 Lean 프로세스에 전달하지 않습니다.

호출 횟수·요청·후보 크기 제한과 실제 응답 비용 기록은 구현되어 있습니다.
비용을 알 수 없으면 재시도 없이 중단합니다. 실제 OpenRouter 연결 검증, 달러 비용의 사전 상한,
외부 라이브러리 환경 연결, OS 수준 격리와 중단 후 재개는 후속 작업입니다.
