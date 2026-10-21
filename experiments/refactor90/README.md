# Refactor90 실험

기존 warm-up 리팩터링 실험의 준비·검증·집계 스크립트입니다.
원본·후보·선택 근거·측정값은 `runs/refactor90/`에 보존했습니다.

코드는 기존 경로 구성을 요구하므로 `data/README.md`의 복원 절차를 먼저 수행합니다.
예: `python3 scripts/corpus.py legacy --script refactor90/collect_results.py`.
집계 결과는 복원 공간의 `refactor90/`에 생성되며 보관된 과거 결과를 덮어쓰지 않습니다.
Lean 환경 준비·검증 스크립트는 해당 toolchain과 의존성이 필요합니다.

과거 측정 JSON의 경로는 당시 루트를 기준으로 합니다. 실제 파일은 `runs/refactor90/`에 있으며
완전한 기존 경로 구조는 legacy 작업 공간에서 복원됩니다. 공식 Arena 통과 여부와
로컬 compiler 검증 여부는 기존 기록에서 구분한 상태를 그대로 유지합니다.
