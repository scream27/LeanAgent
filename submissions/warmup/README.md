# Warm-up 첫 제출 준비 후보

`best/P01.lean`부터 `best/P15.lean`까지 담당자별 최종 후보를 모은다. 대시보드의 대표 후보와 파일 내용 및 SHA-256이 같다. 원본 LeanAgent 자료는 그대로 보존한다.

`best`는 담당자 최종본을 선택했다는 뜻이다. 후보 간 점수 최적화, 모든 지정 버전 통과, Track1 API 비용·생성 요건 충족을 뜻하지 않는다. 아직 공식 제출하지 않았다.

- `best/`: 제출 준비용 선언·증명. P12의 보조 증명은 대상 정리 내부의 `have`로 포함한다.
- `manifest.json`: 작성자, LeanAgent 원본 경로·커밋·해시, 후보 해시, 검증 상태·지정 버전.
- 공식 명제·헤더·소스 위치: manifest의 `benchmarkSnapshot`이 가리키는 기존 벤치마크 JSONL. 전체 문맥은 지정된 라이브러리 커밋에서 복원한다.

이 파일들은 고정된 문제 문맥에 넣는 후보이므로 모두 독립 실행 파일인 것은 아니다. P14·P15의 계측용 헤더·후행 명령은 후보에서 제외했으며 원본 LeanAgent 파일에서 확인할 수 있다. API 요청 형식은 API를 연결할 때 별도로 준비한다.

## 지정 환경 재검증

P10·P11·P12·P13·P14·P15의 환경은 `.github/workflows/warmup-verification.yml`의 **Verify pinned warmup environments**를 수동 실행해 복원한다. ArkLib v4.28–v4.31 및 Mathlib v4.25–v4.27을 각각 별도 Linux runner에서 준비한다. `verification-inputs.json`은 위 benchmarkRevision에서 가져온 공식 명제·원본 증명·헤더와 버전별 소스 커밋을 고정한다. 실행 [40301978929](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/actions/runs/40301978929)의 전체 7개 summary로 결과를 갱신했으며, P12를 포함한 모든 등록 원본·후보가 지정 버전을 통과했다.

현재 P07·P12 best 파일은 각각 SHA-256 `a5463ce0c227809919c02f9dee135565a88d06ff5a4f0aadaf1a45f5c9e4a07e`, `cbc9d9819e788a9c7f1bfa917c17edfd7b31907a3b7c17b765b0a3eddff1abc4`인 수정 후보다. 패치한 평가기로 macOS arm64의 고정 커밋·의존성에서 P07(v4.31.0/v4.32.0/v4.33.0-rc2), P12(v4.29.0/v4.30.0/v4.31.0)의 원본·후보 컴파일·공리 검사와 각각 3회 측정을 통과했다. 후보·manifest·대시보드 proof와 해시를 동기화했으며, 이전 후보의 측정값·통과 상태는 새 후보에 이월하지 않았다. P12는 이후 Linux 공통 환경의 세 버전에서도 통과하여 새 측정값을 반영했다. 대표 v4.31.0에서 원본 1,353토큰/9,199 HB, 후보 747토큰/3,501 HB이며 호환성은 3/3이다. macOS 측정값은 게시하지 않았고, P07은 현재 Linux warmup 워크플로의 대상에 포함되지 않아 `pending`을 유지한다.

`scripts/verify_warmup_pins.py`는 고정 커밋을 checkout하고, 해당 Lean 컴파일러 설치 → 공식 Mathlib 캐시 복원 → 필요한 모듈 빌드 → 의존성 커밋 대조를 수행한다. 원본이 통과한 환경에서만 후보를 PR3 평가기로 측정한다. 후보는 대시보드의 파일 해시와 대조하고, 선택 후보는 `best/` 파일과도 일치해야 한다. 세 번의 독립 실행 중앙값과 허용 공리 검사는 기존 평가기와 같다.

### Cardinality 표기 사전검사 수정

실행 `40278829841`에서 P12의 공식 원본에 있는 `#(filter …)`가 PR3 사전검사의 `#` 전체 금지에 걸렸다. 세 지정 버전 모두 원본 사전검사에서 중단되어 수정 후보는 평가하지 못했다. Actions 성공은 검증 시도와 artifact 저장의 완료이며 증명 통과를 뜻하지 않는다.

`scripts/warmup_evaluator.py`는 평가기 커밋 `c18ec56682462847e2f4d8b6d60aa79ec071a10b`를 복원하고 `tokens.py`의 `|#|` 한 곳만 `|#(?![({])|`로 바꾼다. 버전은 `lean-declaration-cardinality-v1`이며, 복원 전후 파일의 고정 SHA-256을 확인한다. 공백 없이 붙은 `#(`·`#{`만 허용하고, 내부·후행 코드의 금지 명령과 기존 금지 항목은 계속 검사한다. 공식 원본, 후보, 토큰 계산, Lean 실행·heartbeat 계측·공리 검사는 변경하지 않는다. 이 사전검사는 샌드박스가 아니며 문법·증명 유효성은 Lean 검증으로 확인한다.

summary에는 기준 커밋 `evaluatorRevision`, 패치 버전 `validatorVersion`, 실제 `tokens.py` 해시 `validatorSha256`을 기록한다. 게시기는 세 값이 현재 설정과 일치하는 summary만 받으며, 게시한 `verification-results.json`은 schemaVersion 2로 이 정보를 전체 및 실행별로 보존한다. 기존 실행의 summary에는 패치 정보가 없으므로 새 결과와 섞어 게시할 수 없다. 새 설정으로 전체 7개 환경을 다시 실행한 뒤 반영한다. 회귀 검사는 다음 명령으로 실행하며 warmup 워크플로에서도 의존성 설치 전에 수행한다. Lean 설치나 네트워크는 사용하지 않는다.

```sh
python3 -m unittest discover -s tests -p test_warmup_validator.py
```

### 검증 결과 반영

메모리 기본 한도는 6 GiB이며, 원본 실행에서 Lean 메모리 예외가 확인되면 준비된 환경에서 8 GiB로 한 번 재시도한다. 이 경우 후보도 같은 8 GiB 설정으로 측정하고 실제 명령을 fingerprint에 남긴다. 메모리 한도·시간 초과는 증명 오류와 구분한다.

완료된 작업의 `warmup-<source>-<version>` artifact에는 준비 로그, 실제 컴파일 명령·오류, 측정 결과와 환경 fingerprint가 들어 있다. 전체 7개 summary를 내려받은 뒤 `python3 scripts/publish_warmup_verification.py <summary.json ...>`으로 반영한다. 이 스크립트는 모든 지정 버전과 후보 해시가 맞는지 확인한 뒤 대시보드와 manifest를 갱신한다. 환경 구축 실패나 미완료 artifact로는 게시할 수 없다. 원본 실패와 후보 실패는 검증 결과에 구분해 남긴다.

`verification-results.json`에는 게시한 결과와 GitHub Actions 실행 ID를 보존한다. 상세 실험 로그는 작업 브랜치에 기록 후 삭제하며, main에는 후보·재현 스크립트·검증 요약만 유지한다. Actions artifact 보관 기간은 30일이며, 이후에도 작업 브랜치의 실험 기록 커밋 `8baf521`에서 `experiments/warmup-environment-repair/`의 상세 로그를 복구할 수 있다.

기존 웜업 수집 사본·보조 스크립트·원시 로그는 정리 요청에 따라 최종 트리에서 제거했다. 평가 입력에 등록되지 않은 문제의 측정과 근거 링크는 기존 대시보드 데이터를 유지하며, 과거 로그는 삭제 전 커밋에서 확인한다. 후보를 변경하면 새로 검증한 뒤 best 파일·manifest 해시·대시보드 후보를 함께 갱신한다.


## 첫 업로드 파일과 남은 수정 범위 (2026-10-23)

업로드할 파일은 `submission.jsonl`이다. UTF-8 JSONL이며 각 줄에는 공식 benchmark의 `name`과 명제를 포함한 전체 Lean 선언인 `proof`만 들어 있다. `manifest.json`, `submission.audit.json`, 대시보드 JSON은 업로드 파일이 아니다.

저장된 `submission.jsonl` 묶음은 **14개 팀 best + P12 공식 원본**이다. 생성 당시 P12 팀 후보는 최상위 `private lemma` 세 개와 `omit` 문맥 변경을 포함하므로 그대로 넣지 않았다. 대신 고정 benchmark의 `src`를 그대로 사용했다. P12 원본의 공식 평가 통과나 점수는 아직 확인하지 않았으며, 해당 행을 팀 리팩터 성과로 취급하지 않는다. 이후 수정된 P12 후보는 이 파일에 아직 반영하지 않았다.

재생성:

```bash
python3 scripts/export_warmup_submission.py --p12-reference
```

로컬에 manifest의 `benchmarkSnapshot` 파일이 있어야 한다. 배포 저장소에는 benchmark 원본이 포함되지 않을 수 있으므로 `benchmarks/README.md`의 출처를 확인한다. `--p12-reference`는 대체 사용을 명시적으로 선택하는 옵션이다. 수정된 P12 후보는 이 옵션 없이 패키징할 수 있는 단일 선언 형태이며, 지정 환경 검증이 완료되면 이 옵션 없이 생성한다. 패키징 검사를 통과한 것만으로 Lean 검증 통과를 뜻하지 않는다.

검사 기록 `submission.audit.json`에는 제출 파일·각 proof의 SHA-256, 공식 규칙 revision, 선택 출처, 원본 대체 여부와 로컬 검증 상태가 있다. 생성기는 정확한 15개 이름·중복·manifest 해시·명제 보존·공식 업로드 금지 패턴·추가 선언을 검사한다. 이 검사는 Lean 컴파일이나 공식 평가를 대체하지 않는다.

| 우선순위 | 수정 범위 | 완료 조건 |
|---|---|---|
| P12 팀 후보 제출 전 필수 | 보조정리 세 개를 내부 `have`로 이동하고 후보의 최상위 `omit` 제거 완료. 공식 statement와 동일하며 manifest·대시보드 후보 해시를 동기화함 | ArkLib v4.29/v4.30/v4.31에서 원본·후보 검증 통과 및 Linux 측정 결과 반영 완료 |
| P12 검증 연결 | 공식 P12 입력 및 `ArkLib.Data.CodingTheory.ProximityGap.DG25.MainResults` 빌드 타깃 연결 완료. 게시기는 등록 입력을 따라 P12도 처리함 | 실행 40301978929의 전체 7개 summary 반영 완료. `submission.jsonl` 재생성은 별도 진행 |
| 나머지 검증 보완 | P03(v4.29.1/v4.27.0), P07(v4.33.0-rc2), P08(v4.33.0-rc2/v4.30.0), P09(v4.33.0-rc2)의 환경 준비 | 실제 검증 결과에 따라 상태 갱신. 현재 JSONL에 포함되어 있지만 전체 버전 통과를 보장하지 않음 |
| 공식 점수 표시 | `dashboard/src/lib/model.ts`와 결과 데이터에 공식 결과 표시 경로 추가 | 로컬 실험 평균과 분리해 미제출·실패 0점 포함 15문제 평균, 공식 heartbeat 기준 및 worker 결과 사용 |
| 최종 참가 요건 | `docs/architecture.md`의 OpenRouter 실행·비용 장부·재현 하네스·보고서 계획 구현 | 문제당 $3에 재시도/폐기 후보 포함, 모델 공개, 재현 코드와 OpenReview 보고서 준비. 지금 업로드 가능하다는 사실을 비용 요건 면제로 해석하지 않음 |

공식 홈페이지는 증명 업로드와 코드 제출을 분리한다. 코드는 2026-11-01부터 접수하며 코드·보고서 마감은 2026-11-08이다. 첫 업로드 시 발급되는 submission key를 보관하고, 재제출은 기존 리더보드 결과를 교체하므로 전체 묶음을 사용한다. 이 작업에서는 실제 업로드를 수행하지 않았다.

규칙 확인 기준: [공식 app.py, 8fdaaaa](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/blob/8fdaaaa25b993ae8d894e9bb756c3ae222b58507/app.py), [공식 홈페이지](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena).
