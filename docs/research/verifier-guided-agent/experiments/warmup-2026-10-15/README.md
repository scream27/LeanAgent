# Warm-up 전체 프롬프트 모의 실험

사용자 승인: 이 대화의 모델로 생성, 별도 모델 API 호출 없음. `o200k_base`로 원본·후보를 함께 계측하고 Lean heartbeat와 합친 **로컬 모의 점수**를 사용한다. 모든 지정 버전에서 같은 body를 검증한다. 8번은 정상 재귀와 기존 self-reference 정책이 충돌하므로 사용자 지시에 따라 원본 보존, 정책 변경 보류. Escalation은 프롬프트 출력까지만 한다.

## 실험 단위와 재현

- `prompts.json`: P1 구조 유지 간소화 / P2 구조 개선 / P3 비용 축소.
- `inputs/`: 15문제 × 3개 프롬프트 입력. 데이터 원문과 문제 metadata만 제공한다.
- `freeze_candidates.py`: 이 대화 모델이 작성한 1회 후보를 재현하는 edit 기록. API 생성기가 아니며, 검증 결과로 후보를 고치는 알고리즘도 아니다.
- `candidates.jsonl`: 최초 검증 전에 고정한 45개 슬롯. 8번 세 슬롯은 제외 대조군이다. 확신할 변경을 찾지 못한 후보도 원본 그대로 저장했다.
- `prepare_all.py`: 지정 commit/toolchain별 준비, 빌드, 실행. 이 실험이 만든 `.lake`/toolchain 캐시만 작업 후 회수한다. 기존 사용자 프로젝트는 회수하지 않는다.
- `run_sweep.py`: 전체 파일 검사, 대상 공리 의존성, 계측, 고정 로컬 연산 및 동일 derived body의 버전별 replay.
- `report.py`: 관찰 결과 집계, 원본 대비 strict improvement 선택, offline policy prompt 생성.
- `REPORT.md`, `results.csv`, `results.json`, `selected.json`: 집계 결과. `baseline_complete=false`인 선택 기록은 검증된 최종 제출로 사용하지 않는다.
- `policy/<ID>/<P>/prompt.txt`: 필요한 경우 출력한 escalation 요청. 모델에 전송하지 않았다.
- `escalation_policy.py`: 이 실험에 사용한 정책의 고정 사본. `manifest.json`에 해시를 기록했다.
- `audit_results.py`, `audit.json`: 고정 입력 해시, 선택 proof의 검증 기록, 버전·계측 누락, API 미호출을 감사한다.
- `export_artifacts.py`: GitHub 공유용 텍스트 기록을 복사한다. toolchain, 의존성 캐시, `.olean` 등 빌드 바이너리는 제외한다.

원본 JSONL은 공개 Space revision `56aa7b8`에서 받은 파일과 바이트 단위로 일치했다. `reference/benchmark_heartbeats.jsonl`에 공개 heartbeat 기준값을 보존했다. 원본 proof 길이와 공개 heartbeat는 공식 값으로 표에 별도 표시한다.

모든 후보는 같은 대화 모델이 같은 대화 문맥에서 작성했다. 독립 세션으로 통제한 모델 실험이 아니다. 1·2번은 이전 대화에서 검토한 문제이므로 사전 노출을 표시했다. 최초 생성 이후 모델이 proof를 재작성하는 repair/optimization은 수행하지 않는다. 검사 코드의 버그 수정과 고정된 로컬 tactic 실행은 구분한다.

## 계측·선택 계약

토큰은 tiktoken 0.14.0, `o200k_base`로 proof body 전체(공백·주석 포함)를 센다. 공식 `proof_length`와 단위가 다르므로 공식 길이를 로컬 점수 분모로 혼합하지 않는다. Heartbeat는 `IO.getNumHeartbeats` 차이를 1000으로 나눈 값이며 대상 선언만 `Elab.async false`로 elaboration한다. 원래 resource options는 유지한다. 원본과 후보를 같은 방법으로 계측한다. 계측용 Lean 코드는 제출 proof에 포함하지 않는다.

목록의 첫 번째 지정 버전을 token/HB 기준 환경으로 사용하고, robustness는 모든 지정 버전에서 동일 body가 통과한 비율이다. 기본 유효성은 기준 버전에서 확인한다. 원본 모든 버전 검증과 비교 가능한 계측이 완결되어야 종합 점수를 만든다. 원본·후보의 기본 axiom 집합도 비교하여 새 의존성을 추가한 후보는 선택하지 않는다.

`combined = (100*(1-L/L0) + 100*(1-H/H0) + 100*passed/total)/3`.
원본이 모든 버전을 통과하면 원본 점수는 33.333…이다. 공식 worker와 동등한 측정기라고 주장하지 않는다. raw 후보의 개선/악화와, 로컬 처리 뒤 최종 선택/원본 fallback을 따로 기록한다. invalid는 악화된 유효 proof와 구분한다. 계측/환경 미완료는 unresolved이며 원본 제출 성공으로 바꾸지 않는다.

## 고정 로컬 처리 v1

valid 후보에서는 처음 두 개의 단독 `simp`/`simp_all`/`aesop` 위치에 `?`를 붙여 제안을 얻는다. 한 줄로 확실히 추출할 수 있는 `simp only`, `simp_all only`, `exact` 제안만 새 후보로 재검증한다. 다중 줄 aesop script 추출은 미구현이며 성공했다고 표시하지 않는다. 원후보와 각 추출 후보를 모두 보존한다. 단순 문자열 길이로 winner를 선택하지 않는다.

invalid 후보에서는 첫 진단이 가리키는 본문 내 한 줄을 대상으로 하되, 들여쓴 후속 블록이 있거나 case header이면 본문 전체를 대상으로 한다. `assumption`, `rfl`, `omega`, `simp?`, `exact?`, `aesop?` 순으로 시도하고 전체 replay 성공 시 멈춘다. 작은 오류 위치 판별은 텍스트 heuristic이며 trusted tactic state가 아니다. 사용할 수 없는 tactic 오류도 로그에 남긴다. 실패하면 body scope escalation 프롬프트를 출력한다.

로컬 `?` 탐색 proof 자체는 진단용 기록이며 최종 선택 pool에서 제외한다. 추출한 명시적 proof만 제출 후보로 평가한다. 9번에서는 `exact?`가 일반 검증에서 성공했지만 동기 계측 문맥에서는 실패했고, 추출한 `exact` proof는 양쪽에서 통과했다. 탐색 성공만으로 최종 후보를 채택하면 안 되는 실제 사례다. 추출 proof도 점수가 원본보다 낮아 채택하지 않았다.

로컬 후보는 첫 지정 버전에서 생성하고 다른 버전에는 같은 body를 그대로 재실행한다. 버전별 서로 다른 수리를 묶어 robustness를 만들지 않는다. 검증기 timeout은 실행당 180초의 운영 설정이며 대회의 제한으로 주장하지 않는다. timeout은 수학적 invalid로 확정하지 않는다.

## 검증기 한계와 수정 이력

- 고정 원문의 body 위치만 교체한다. 본문 내 명령 삽입은 간단한 거부 검사와 실제 전체 Lean 검사로 확인한다. 일반적인 악성 입력에 대한 완전한 Lean AST firewall은 아직 아니다. 이 실험 후보는 저장된 model-authored body로 전부 감사 가능하다.
- module 파일 내 `#print axioms` 제한을 발견했다. 해당 파일은 `.olean`으로 만들고 별도 probe 파일에서 읽는다. 원본 module을 삭제하지 않는다. 계측 helper는 별도 사본에만 넣는다.
- copyright comment 다음에 오는 `module`을 고려하도록 계측 import 삽입 위치를 수정했다. 초기 검사기 실패는 proof 실패로 집계하지 않는다.
- ArkLib 10번에서는 계측 wrapper가 후속 `omit ... in`의 section-variable 처리에 영향을 주었다. 전체 파일은 먼저 계측 없이 검증하며, 별도 계측 사본은 대상 선언 직후 `#exit`로 종료하도록 수정했다. 이 변경은 제출 proof에 들어가지 않는다. Lean 4.32에서 열린 namespace 안의 `#exit` 종료 동작도 확인했다.
- ArkLib 10번 구버전은 `have h_elemenet_Y_bad :  y_of_x`의 추가 공백 하나가 benchmark와 다름을 직접 diff로 확인했다. 이 정확한 body 내 차이만 대응한다. statement/주변 문맥을 fuzzy matching하거나 수정하지 않는다.
- 처음 수집한 오류 결과는 `results.before_runner_fix.json`에 보존한다. proof 후보는 검사기 수정 때문에 바꾸지 않는다.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -B run_sweep.py strata v4.26.0 ../strata
python3 -B prepare_all.py --only=physlib:v4.32.0
python3 -B report.py
python3 -B audit_results.py
```

`prepare_all.py`는 다운로드와 로컬 빌드를 수행한다. 전체 재현에 필요한 공간·시간은 환경에 따라 크다. 결과 파일은 실행 상태에 따라 다시 집계할 수 있으며, 데이터/프롬프트/후보 해시는 `manifest.json`에 기록한다.

보고서 재집계와 감사는 Python 표준 라이브러리만으로 실행할 수 있다. 검증 재실행에는 elan/lake와 지정 환경이 필요하다. Strata 4.26은 최초 실험의 기존 checkout 및 사용자 toolchain을 재사용하므로 위 명령의 `../strata`를 해당 고정 checkout 경로로 지정한다. 나머지는 `prepare_all.py`로 순차 준비한다. 이미 기록된 성공 결과는 재사용하므로 완전한 재실험은 별도 디렉터리에 `runs/` 없이 코드·입력·후보를 복사하여 실행한다.

검증 로그의 절대 경로는 실행 당시 기록으로 보존했다. 보고서는 현재 디렉터리의 `runs/`에서 해당 로그를 읽는다. 원문 source snapshot의 저작권 표기는 보존했으며 관련 프로젝트 라이선스는 `reference/licenses/`에 모았다.
