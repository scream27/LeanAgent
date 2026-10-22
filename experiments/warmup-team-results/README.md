# 웜업 팀 실험 결과

LeanAgent에 공유된 팀원 후보를 모아 같은 기준으로 재검증하고, 대시보드의 P01–P15에 연결한다.
정답 집합이나 대회 제출물이 아니다. 과거 CLI·수작업 실험의 증명 검증과 Track1 API 실행의 비용·생성 재현은 별개다.

## 보관 구조

- `manifest.json`: 15문제, 담당자, 수집 후보, 대표 표시 후보와 출처.
- `candidates/Pxx/<작성자-기록>/`: 원본 자료, 추출한 선언, 출처·해시. 원본 보고서는 수정하지 않는다.
- `configs/Pxx/`: 보관된 공식 문제 스냅샷의 명제·원본·지정 버전.
- `runs/warmup-team-results/<실행 ID>/`: 재검증 입력·환경·컴파일 로그·측정값. 이전 실행은 덮어쓰지 않는다.
- `dashboard/public/data/warmup-team-results.json`: 완료된 검증 실행에서 생성한 화면용 데이터.

전체 팀원 자료를 복사하지 않고 후보와 근거가 있는 자료를 가져온다. 보고서에 있는 코드는 블록 번호와 추출 방식을 기록한다.
`sourceState=working-tree-snapshot`은 LeanAgent HEAD에 없는 로컬 파일이다. 이 경우 `sourceCommit`은 작업 트리의 기준 커밋일 뿐 파일이 포함된 커밋이 아니며, 복사한 원본과 SHA-256이 정확한 출처다.

11번은 현재 개선 후보가 없다. `best.lean`이 원본 fallback인 기록은 팀원 성과로 등록하지 않는다.
12번의 보조정리는 후보 전체에 보존한다. PR3의 단일 선언 계약으로 검증할 수 없으면 `검증기 지원 대기`로 남긴다.
14·15번의 파일 헤더는 원본 자료와 `preamble.lean.txt`에 보관하며 고정 문맥에 임의로 추가하지 않는다.

## 대표 표시 기준

담당자가 공유한 최종본을 우선 표시한다. 담당자 후보가 없으면 기존 실험에서 명시적으로 선택된 팀 후보를 사용한다.
대표 후보 ID와 이유는 manifest에 고정하고, 재검증 점수에 따라 자동 교체하지 않는다. 다른 후보도 상세 화면에서 코드·결과·출처를 확인할 수 있다.

## 검증 기준과 한계

PR #3의 `refactor_eval.LeanEvaluator`를 커밋 `c18ec56682462847e2f4d8b6d60aa79ec071a10b`로 고정해 중앙 캐시에 추출한다.
PR3를 이 브랜치에 병합하거나 평가 정책을 변경하지 않는다. 여기서는 탐색·자동 최종 선택 루프 대신 기존 후보의 재측정 기능만 사용한다.

1. 공식 원본 선언과 지정 커밋의 전체 소스 문맥이 일치하는지 확인한다.
2. 후보 명제는 원문 바이트를 보존해야 한다. 단일 tactic 선언 외 형태는 현재 평가기 지원 대기로 구분한다.
3. 원본의 비계측 컴파일과 3회 독립 계측이 통과한 환경에서만 후보를 평가한다.
4. 후보도 비계측 컴파일 후 3회 계측한다. 허용 공리는 `propext`, `Classical.choice`, `Quot.sound`다.
5. 토큰은 `lean-source-anchored-v1`, HB는 대상 선언 raw counter / 1000의 내림값을 3회 측정한 중앙값이다.
6. 원본 선언에 붙은 문서 주석·`set_option … in`·`omit … in`은 양쪽에 동일하게 유지한다. 계측 코드는 이 문맥을 가로채지 않도록 배치한다.

측정 대표 버전은 수집 점수를 보기 전에 출처별로 고정한다: Strata 4.26.0, PhysLib·CSLib 4.32.0, ArkLib 4.31.0, PutnamBench 4.26.0.
다른 버전의 값을 섞거나, 기준 버전이 실패했다고 통과한 버전으로 대체하지 않는다. 모든 지정 버전의 호환성 검사는 따로 기록한다.
일부 버전만 통과했어도 대표 버전에서 원본·후보 측정이 완료되면 해당 환경의 개선율은 표시하되 `일부 버전 검증`으로 표시한다. 미완료 호환성·전체 종합 점수는 산출하지 않는다.

기존 보고서 수치나 무효 처리된 과거 HB 기록은 새 점수로 사용하지 않는다.
컴파일러가 없거나 원본부터 실패하면 환경 준비 실패, 후보 컴파일/공리가 실패하면 증명 검증 실패로 구분한다. 시간 초과는 통과나 0점이 아니다.

현재 실행은 로컬에 준비된 라이브러리 캐시를 재사용한다. source revision·의존성 lock·컴파일러 해시·실제 명령·문맥·로그를 기록하지만, 전체 의존성을 새 기계에서 다시 빌드한 검증은 아니다.
macOS에서는 검증 프로세스의 네트워크·파일 쓰기를 차단한다. 호스트 읽기 접근까지 격리한 에이전트 실행을 뜻하지 않는다.
이 후보 디렉터리와 전체 `runs/`를 독립 에이전트 탐색 입력에 노출하지 않는다.

## 실행

저장소 루트에서 중앙 환경을 적용하고 Python 3.10+를 사용한다. 아래 경로는 사용자의 실제 LeanAgent 경로로 지정한다.

```sh
source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent-LeanRefactorArena
python3 experiments/warmup-team-results/collect.py --leanagent ../LeanAgent
python3 experiments/warmup-team-results/verify.py --leanagent ../LeanAgent \
  --run runs/warmup-team-results/<새-실행-ID>
python3 experiments/warmup-team-results/export.py \
  --run runs/warmup-team-results/<완료된-실행-ID>
```

검증은 모델을 호출하거나 환경을 자동 다운로드하지 않는다. 기존 기록에서는 컴파일러·라이브러리 경로만 읽고 과거 실행 명령을 실행하지 않는다.
`--environments <JSON>`으로 환경 위치를 명시할 수 있다. 형식은 실행 폴더의 `environments.local.json`을 참고한다.
`--only 4 5`로 특정 문제를 새 실행에서 재검증할 수 있다. export에 `--run`을 여러 번 주면 뒤쪽 실행이 해당 문제의 전체 결과를 대체한다. 실패도 그대로 대체하며 좋은 점수만 골라 합치지 않는다.
완료되지 않은 실행, 변경된 후보/manifest, 서로 다른 평가기 버전, 15문제 미달 기록은 내보내지 않는다.

```sh
python3 -m unittest discover -s experiments/warmup-team-results -p 'test_*.py'
npm --prefix dashboard test
npm --prefix dashboard run data:check
npm --prefix dashboard run build
```

## 이번 로컬 확인 결과 (2026-10-22)

20개 후보를 수집했고, 다음 네 실행을 순서대로 합쳐 화면 데이터를 만들었다.

```sh
python3 experiments/warmup-team-results/export.py \
  --run runs/warmup-team-results/20261022-final-main \
  --run runs/warmup-team-results/20261022-parallel-remaining-01 \
  --run runs/warmup-team-results/20261022-parallel-remaining-02 \
  --run runs/warmup-team-results/20261022-final-p06
```

| 상태 | 문제 |
| --- | --- |
| 모든 지정 버전 검증 완료 | 1, 2, 4, 5, 6 |
| 대표 환경 측정 완료, 일부 지정 버전 미준비 | 3, 7, 8, 9 |
| 고정 의존성 환경 미준비 | 10, 13, 14, 15 |
| 개선 후보 없음 | 11 |
| 보조정리 포함 후보의 평가기 지원 필요 | 12 |

10번은 ArkLib·CompPoly·VCVio 등 지정 의존성 빌드가 필요하다. 13–15번은 지정 Mathlib checkout 및 `import Mathlib` 산출물이 필요하다.
3번은 Strata 4.27/4.29.1, 7·9번은 CSLib 4.33-rc2, 8번은 CSLib 4.30/4.33-rc2 환경이 추가로 필요하다.
다른 버전으로 대체하거나 기존 보고서의 통과 값을 가져오지 않았다.

`prepare_remaining.py`는 기존 부분 캐시를 중앙 캐시의 파일 단위 overlay로 합친다. Lean이 첫 namespace 경로를 고른 후 다른 경로의 누락 파일을 찾지 못하는 경우를 피하기 위한 구성이다.
준비 근거는 `runs/warmup-team-results/preparation-report.json`, 미준비 환경은 `remaining-environment-audit.json`에 있다.
기존 소스 checkout을 바꾸지 않고, 복구가 필요한 문제만 새 실행에 기록했다.

```sh
python3 experiments/warmup-team-results/prepare_remaining.py \
  --environments runs/warmup-team-results/environment-overrides.local.json \
  --output runs/warmup-team-results/remaining-environments.local.json
```

수집 후보와 로그는 로컬 검증 결과다. 대시보드 배포와 공식 평가 제출은 별도로 진행한다.
