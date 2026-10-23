# Warm-up 첫 제출 준비 후보

`best/P01.lean`부터 `best/P15.lean`까지 담당자별 최종 후보를 모은다. 대시보드의 대표 후보와 파일 내용 및 SHA-256이 같다. 원본 LeanAgent 자료는 그대로 보존한다.

`best`는 담당자 최종본을 선택했다는 뜻이다. 후보 간 점수 최적화, 모든 지정 버전 통과, Track1 API 비용·생성 요건 충족을 뜻하지 않는다. 아직 공식 제출하지 않았다.

- `best/`: 제출 준비용 선언·증명. P12는 필요한 새 보조정리까지 포함한다.
- `manifest.json`: 작성자, LeanAgent 원본 경로·커밋·해시, 후보 해시, 검증 상태·지정 버전.
- 공식 명제·헤더·소스 위치: manifest의 `benchmarkSnapshot`이 가리키는 기존 벤치마크 JSONL. 전체 문맥은 지정된 라이브러리 커밋에서 복원한다.

이 파일들은 고정된 문제 문맥에 넣는 후보이므로 모두 독립 실행 파일인 것은 아니다. P14·P15의 계측용 헤더·후행 명령은 후보에서 제외했으며 원본 LeanAgent 파일에서 확인할 수 있다. API 요청 형식은 API를 연결할 때 별도로 준비한다.

## 지정 환경 재검증

P10·P11·P13·P14·P15의 환경은 `.github/workflows/warmup-verification.yml`의 **Verify pinned warmup environments**를 수동 실행해 복원한다. ArkLib v4.28–v4.31 및 Mathlib v4.25–v4.27을 각각 별도 Linux runner에서 준비한다. `verification-inputs.json`은 위 benchmarkRevision에서 가져온 공식 명제·원본 증명·헤더와 버전별 소스 커밋을 고정한다.

`scripts/verify_warmup_pins.py`는 고정 커밋을 checkout하고, 해당 Lean 컴파일러 설치 → 공식 Mathlib 캐시 복원 → 필요한 모듈 빌드 → 의존성 커밋 대조를 수행한다. 원본이 통과한 환경에서만 후보를 PR3 평가기로 측정한다. 후보는 대시보드의 파일 해시와 대조하고, 선택 후보는 `best/` 파일과도 일치해야 한다. 세 번의 독립 실행 중앙값과 허용 공리 검사는 기존 평가기와 같다.

메모리 기본 한도는 6 GiB이며, 원본 실행에서 Lean 메모리 예외가 확인되면 준비된 환경에서 8 GiB로 한 번 재시도한다. 이 경우 후보도 같은 8 GiB 설정으로 측정하고 실제 명령을 fingerprint에 남긴다. 메모리 한도·시간 초과는 증명 오류와 구분한다.

완료된 작업의 `warmup-<source>-<version>` artifact에는 준비 로그, 실제 컴파일 명령·오류, 측정 결과와 환경 fingerprint가 들어 있다. 전체 7개 summary를 내려받은 뒤 `python3 scripts/publish_warmup_verification.py <summary.json ...>`으로 반영한다. 이 스크립트는 모든 지정 버전과 후보 해시가 맞는지 확인한 뒤 대시보드와 manifest를 갱신한다. 환경 구축 실패나 미완료 artifact로는 게시할 수 없다. 원본 실패와 후보 실패는 검증 결과에 구분해 남긴다.

`verification-results.json`에는 게시한 결과와 GitHub Actions 실행 ID를 보존한다. 상세 실험 로그는 작업 브랜치에 기록 후 삭제하며, main에는 후보·재현 스크립트·검증 요약만 유지한다. Actions artifact 보관 기간은 30일이며, 이후에도 작업 브랜치의 실험 기록 커밋 `8baf521`에서 `experiments/warmup-environment-repair/`의 상세 로그를 복구할 수 있다.

기존 웜업 수집 사본·보조 스크립트·원시 로그는 정리 요청에 따라 최종 트리에서 제거했다. 이번에 재검증한 5문제 외의 측정은 기존 대시보드 데이터를 유지하며, 과거 로그는 삭제 전 커밋에서 확인한다. 후보를 변경하면 새로 검증한 뒤 best 파일·manifest 해시·대시보드 후보를 함께 갱신한다.
