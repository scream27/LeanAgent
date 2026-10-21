# 공식 벤치마크 스냅샷

`arena/<revision>/`에 수집 당시 공식 Arena 파일과 `snapshot.json`을 보관합니다.
`snapshot.json`의 URL·수집 시각·해시로 출처를 확인합니다. 이 스냅샷은 현재 최신 규칙이라는 뜻이 아닙니다.

추가로 수집한 여섯 라이브러리의 코퍼스는 `data/corpora/`에서 별도로 관리합니다.
공식 스냅샷의 원본 파일은 Git에서 제외하고 출처 manifest만 관리합니다.
다른 환경에서는 manifest에 명시된 revision의 파일을 받아 SHA-256을 확인해야 합니다.
