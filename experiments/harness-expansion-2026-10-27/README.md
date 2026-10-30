# 공용 하네스 확장 실험 (2026-10-27)

[읽기 쉬운 보고서](report.html) · [전체 측정/진단 JSON](results.json) · [선택된 전체 선언 JSON](arena-submission.json)

## 범위

Warm-up P4/P5/P6, 각각 대화에서 작성해 미리 고정한 3개 후보를 기존 공용 하네스 fixture backend에 공급한다. 유료 API 호출은 0이다. 실시간 모델의 자율 생성 성능 실험은 아니다. `candidate-freeze.json`은 검증 전 입력 해시를 기록한다. 원본/후보 각각 고정 문맥의 일반 컴파일을 먼저 검사하고 새 프로세스 3회 heartbeat 중앙값으로 선택한다. 최종 선택도 다시 검증한다.

- 공용 하네스: `ba593fc4357ee5c429b8f28f1aac512d05bb4355`, src 수정 없음.
- Physlib: `c48433678e8fb6306ebcd48453300c8e16058a62`, Lean 4.32.0. 세 문제 각각 지정 버전은 이 하나뿐이다.
- 토큰: `lean-source-anchored-v1` (BPE 토큰 아님).
- 공개 리더보드 캡처: `leaderboard/provenance.json`, HTML 및 SSE 원문 보존.
- 이전 P1/P2 결과와 이전 전체15 결과는 별도 실험이다. 혼합 추정값을 공식 점수라고 보고하지 않는다.

## 계측 호환성 실패 및 보정

최초 P4 원본 일반 컴파일은 성공했지만 계측 복사본이 `unexpected token 'set_option'; expected 'lemma'`로 실패했다. 선언 앞 문서 주석이 계측 명령에 붙은 것이 원인이다. 원래 실패 실행은 `../../runs/harness-expansion-2026-10-27/4/raw`에 보존했다.

`run.py`의 evaluator adapter는 계측 복사본에서 목표 선언 바로 앞의 문서 주석 `/--`를 일반 주석 `/- `로 바꾼다. 일반 검증에는 적용하지 않으며, 후보/statement/제출 증명은 바꾸지 않는다. 적용 대상 세 문제 중 P4에서만 1문자가 달라진다. 핵심 하네스를 포크하지 않고 기존 evaluator 확장점에서 처리한다. 현재 렌더 함수의 일시적 교체는 이 순차 실행 전용이며 병렬 스레드용으로 사용하면 안 된다. 보정 후 실행은 `raw-v2` 폴더에 분리했다.

## 재현

저장소 루트에서:

```sh
python3 experiments/harness-expansion-2026-10-27/prepare.py
python3 experiments/harness-expansion-2026-10-27/run.py 4 5 6
python3 experiments/harness-expansion-2026-10-27/summarize.py
python3 experiments/harness-expansion-2026-10-27/report.py
PYTHONPATH=src python3 -m unittest discover -s tests -p test_harness.py
python3 experiments/harness-expansion-2026-10-27/test_adapter.py
```

`prepare.py`는 이 워크스페이스의 기존 Physlib clone을 object source로 사용하며 지정 버전의 toolchain/cache를 내려받는다. 외부 호스트에서는 해당 원격 저장소를 같은 commit으로 clone하여 준비해야 한다. `lean_command.py`의 실행 환경 경로는 이 저장소 기준으로 계산한다. 입력 config는 실행 당시 Python/launcher 절대경로를 포함한다. 다른 호스트에서는 config를 재생성하고 새 실험으로 기록해야 한다.

완료된 결과는 재사용하지만 미완료 폴더에 덮어쓰지 않는다. 처음부터 재실행할 때는 새로운 실행 디렉터리를 사용한다. sealed raw 디렉터리는 수정하지 않는다. `record-replay.json`은 기록의 결정적 재생 확인이며 Lean 재실행이 아니다. 실제 Lean 재검증은 raw-v2/final에 있다.

`observations.json`은 측정 결과를 확인한 뒤 작성한 해석이다. `results.json`은 실제 raw 결과로부터 계산한다. `arena-submission.json`은 새 세 문제만 포함하므로 전체15 제출 파일로 오인하면 안 된다.
