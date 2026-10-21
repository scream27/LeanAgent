# 수집 데이터 재배치 — 2026-10-21

6개 코퍼스의 382,121개 레코드를 출처·revision별 bundle로 재배치했습니다.
기존 코퍼스 폴더의 80,479개 파일은 `data/corpora/`의 102개 파일로 정리했습니다.
이 수치는 별도 원본 보관 archive, upstream Git checkout, 실험 코드와 실행 결과를 제외합니다.

- 원본 7개 archive와 파일별 SHA-256 목록 보존.
- 코퍼스 전체 저장 무결성 및 기존 문제 파일 58,696개의 동일 바이트 복원 확인.
- 각 출처에서 1문제씩 실제 추출해 원래 문제 파일과 대조.
- 공식 Arena 스냅샷 4개 파일의 기존 해시 일치 확인.
- 기존 결과 파일의 해시를 확인한 뒤 위치만 변경.
- 새 저장 도구 테스트 11개 통과.
- 기존 테스트 70개 중 65개 통과, PhysLib native 파서 테스트 5개 오류.
  오류는 `unknown module prefix 'Mathlib'`로, 지정 환경의 Mathlib 빌드 산출물이 없어 발생했습니다.
  이번 작업에서 해당 의존성을 추가 설치하거나 검증 성공으로 처리하지 않았습니다.

`report.json`은 파일 수·보관본·경로 매핑·검증 범위를 기록합니다.
`materialization-checks.json`은 실제로 추출해 확인한 문제 ID를 기록합니다.
`scripts/migrate_corpus_layout.py`는 초기 변환 도구이며 기존 report가 있으면 재실행을 거부합니다.
후속 재배치는 `report.json`의 경로 매핑대로 수행했고, 원본을 다시 해시 검사한 뒤 중복 폴더를 제거했습니다.

Git commit·push와 PR merge는 수행하지 않았습니다. 데이터 사용·공유·복원 절차는 `data/README.md`를 따릅니다.
