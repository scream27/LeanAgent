# Warm-up과 비슷한 길이의 후보

직접 `sorry/admit`가 없는 `:= by` 증명에서 두 조건을 독립적으로 추렸다. Arena 토큰 수는 시작의 `by`를 포함하며 warm-up 공개 길이 15/15를 재현하는 기존 계산값을 사용한다. Heartbeat 측정과 Lean 실행은 하지 않았다.

| 출처 | 모집단 | 200토큰 이상 | 상위 5% 경계 | 상위 5% | 두 조건 교집합 |
| --- | ---: | ---: | ---: | ---: | ---: |
| [strata](strata/README.md) | 580 | 29 | 202 | 29 | 29 |
| [physlib](physlib/README.md) | 7,210 | 612 | 300 | 361 | 361 |
| [cslib](cslib/README.md) | 1,188 | 35 | 151 | 60 | 35 |
| [arklib](arklib/README.md) | 2,121 | 359 | 580 | 107 | 107 |
| [putnambench](putnambench/README.md) | 0 | 0 | — | 0 | 0 |
| [leanpool](leanpool/README.md) | 312,108 | 47,484 | 505 | 15,611 | 15,611 |

## 상위 5% 경계

출처별 모집단 N에서 길이 내림차순 ceil(N/20)번째 정리의 길이를 경계로 잡고, 그 길이의 모든 동률을 포함한다. 따라서 정확히 5%보다 조금 많을 수 있다. 이전 분포 보고서의 선형 보간 P95 숫자와는 정의가 다르다. LeanPool은 경계 동률로 명목 개수보다 5개 더 포함한다.

## 읽는 순서

각 출처 README에 기존 warm-up을 제외한 미리보기 25개 이하를 제공한다. 교집합을 먼저 보고, 그 안에서는 같은 출처의 warm-up 길이에 가까운 순서로 정렬했다. LeanPool은 자체 warm-up이 없어 전체 15개의 길이를 참고한다. 길이만으로 정한 탐색 순서이며 예상 출제 목록이나 의미적 유사도 순위가 아니다.

- `ge200.jsonl.gz`와 `top5pct.jsonl.gz`: 서로 독립적인 전체 증명 레코드. 명제·증명·문맥 위치·해시·버전 정보를 유지한다.
- `*.index.jsonl`: 위 탐색 순서로 정렬한 가벼운 메타데이터. 전체 증명 파일은 원본 inventory 순서다.
- `intersection.index.jsonl`: 두 조건을 모두 만족하는 후보. 같은 길이 척도의 하한 필터이므로 교집합은 더 엄격한 쪽 목록과 같다.
- 원본에 있는 warm-up 1–12번은 두 목록 모두에서 확인했고 `warmup_number`로 표시했다. PutnamBench 원본은 대상이 없으며 [완성된 warm-up 3개](../all_sources/putnambench_warmup_references.jsonl)는 원본 문제집에 섞지 않았다.
- 직접 sorry 제외는 커널·공리 검증 완료를 의미하지 않는다. 버전 간 동일 선언 여부도 이번에는 새로 검사하지 않았다. 필터 밖 원본 정리는 그대로 보존했다.

재생성: `python3 scripts/select_warmup_candidates.py` (저장소 루트에서 실행). 단일 Python 프로세스로 스트리밍하며 원본 정리 파일을 수정하지 않는다.
