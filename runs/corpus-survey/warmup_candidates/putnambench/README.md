# putnambench: warm-up 길이 후보

모집단 0개. 200토큰 이상 0개, 상위 5% 0개, 교집합 0개.

상위 5% 경계: 대상 없음 토큰. 경계 동률을 모두 포함한다. 기존 warm-up도 전체 목록에는 포함하고 번호로 표시한다.

- [200토큰 이상 전체 증명](ge200.jsonl.gz) · [탐색용 인덱스](ge200.index.jsonl)
- [상위 5% 전체 증명](top5pct.jsonl.gz) · [탐색용 인덱스](top5pct.index.jsonl)
- [교집합 인덱스](intersection.index.jsonl) · [먼저 볼 후보 25개 이하](review_first.jsonl)

## 먼저 볼 후보

기존 warm-up을 제외하고 두 조건을 모두 만족하는 후보를 먼저, 그 안에서는 warm-up 길이와의 로그 비율 차이가 작은 순서다. 같은 출처의 warm-up 길이를 사용하며 LeanPool만 전체 15개의 길이를 참고한다. 수학적 내용·tactic·heartbeat 유사도나 출제 확률 순위가 아니다.

| ID | 정리 | 토큰 | 선택 조건 | 가까운 warm-up 길이 | 원문 |
| --- | --- | ---: | --- | ---: | --- |
대상 없음. PutnamBench 원본은 직접 sorry를 포함하므로, 완성된 warm-up 3개는 별도 참조 자료로 사용한다.

원문 문맥·버전·검증 상태는 전체 증명 레코드에 유지된다. `context_file`은 `original_corpus_root` 기준 상대경로이며 `context_path_from_repository_root`는 저장소 루트 기준 경로다. 독립 컴파일 가능한 문제 파일이라고 가정하지 않는다.
