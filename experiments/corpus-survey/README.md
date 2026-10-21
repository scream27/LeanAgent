# 코퍼스 수집·분석 실험

여섯 출처의 선언 추출, 원본 span 보존, tactic·증명 길이 분석과 후보 집합 선정 코드를 모았습니다.

- `scripts/`: 기존 Python·Lean 분석 도구. 복원 작업 공간에서 실행합니다.
- `tests/`: 기존 추출·분석 회귀 테스트.
- `reference/`: 수집 당시 공식 증명 길이 계산 코드와 출처 기록.
- 결과: 저장소 루트의 `runs/corpus-survey/`.

실행법은 `data/README.md`의 기존 실험 재현 절차를 따릅니다.

```bash
python3 scripts/corpus.py legacy --prepare
python3 scripts/corpus.py legacy --script scripts/compare_all_sources.py -- --help
```

기존 보고서의 경로·스크립트 해시는 당시 기록입니다. 저장 형식 변경으로 검증 수준을 올리지 않습니다.
새로운 분석은 복원 공간에서 수행하고, 보존할 결과를 새 `runs/` 하위 폴더에 옮깁니다.
