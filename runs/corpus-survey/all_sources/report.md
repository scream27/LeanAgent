# 여섯 출처의 추출·tactic 비교

모든 통계는 추출한 증명 문자열에 동일한 확장 어휘 집계기를 적용한 근사치다. Lean 빌드·커널 검사·heartbeat 측정은 실행하지 않았다.

PutnamBench 원본의 미완성 문제와 Arena의 완성된 warm-up 참조 증명은 별도로 집계한다. LeanPool은 여러 하위 프로젝트를 포함한 큰 코퍼스이며 단순 합산 점유율로 다른 출처를 평가하지 않는다.

| 출처 | 조사 Lean 파일 | 추출 정리 | 직접 sorry 제외 | 미분리 선언 |
| --- | ---: | ---: | ---: | ---: |
| strata | 377 | 615 | 606 | 0 |
| physlib | 676 | 9,008 | 8,991 | 0 |
| cslib | 181 | 1,692 | 1,692 | 0 |
| arklib | 328 | 2,686 | 2,578 | 0 |
| putnambench | 674 | 672 | 0 | 0 |
| leanpool | 22,324 | 367,448 | 367,448 | 0 |

## 출처별 많이 등장한 tactic

직접 `sorry`가 없는 추출 정리만 사용한다. 이는 공리 검증 완료라는 뜻이 아니다. 각 항목은 **등장 횟수 / 사용 정리 수 (해당 분모 대비 비율)**다. term 겸용 표기·분기·conv·wrapper는 이 상위 표에서 제외했다.

| 출처 | 분모 | 상위 tactic 5개 |
| --- | ---: | --- |
| strata | 606 | `simp` 1,113 / 419 (69.1%); `simp_all` 865 / 330 (54.5%); `apply` 605 / 201 (33.2%); `intros` 566 / 334 (55.1%); `cases` 541 / 228 (37.6%) |
| physlib | 8,991 | `simp` 10,641 / 4,824 (53.7%); `rw` 9,150 / 4,000 (44.5%); `exact` 4,634 / 2,390 (26.6%); `intro` 2,402 / 1,278 (14.2%); `apply` 2,190 / 1,201 (13.4%) |
| cslib | 1,692 | `grind` 1,281 / 635 (37.5%); `exact` 520 / 311 (18.4%); `simp` 504 / 365 (21.6%); `apply` 462 / 216 (12.8%); `obtain` 363 / 192 (11.3%) |
| arklib | 2,578 | `rw` 3,652 / 1,136 (44.1%); `simp` 3,003 / 1,200 (46.5%); `exact` 2,634 / 1,033 (40.1%); `intro` 1,185 / 513 (19.9%); `omega` 1,089 / 387 (15.0%) |
| putnambench | 0 | 집계 가능한 완성 증명 없음 |
| leanpool | 367,448 | `exact` 363,624 / 167,915 (45.7%); `rw` 337,920 / 135,217 (36.8%); `simp` 169,066 / 90,850 (24.7%); `norm_num` 137,881 / 30,625 (8.3%); `intro` 129,077 / 73,066 (19.9%) |
| putnambench_warmup | 3 | `exact` 62 / 3 (100.0%); `simp` 43 / 3 (100.0%); `intro` 36 / 3 (100.0%); `omega` 31 / 2 (66.7%); `rw` 31 / 3 (100.0%) |

## 같은 tactic의 사용 정리 비율

분모는 각 출처의 직접 sorry 제외 추출 정리다. 감지된 tactic이 없는 정리도 분모에 포함한다. 0%는 현재 집계기가 감지하지 않았다는 의미다.

| tactic | strata | physlib | cslib | arklib | putnambench | leanpool |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `simp` | 69.1% | 53.7% | 21.6% | 46.5% | — | 24.7% |
| `rw` | 15.7% | 44.5% | 13.2% | 44.1% | — | 36.8% |
| `simp_all` | 54.5% | 5.4% | 1.3% | 5.2% | — | 1.4% |
| `grind` | 8.3% | 1.7% | 37.5% | 2.8% | — | 0.3% |
| `exact` | 35.6% | 26.6% | 18.4% | 40.1% | — | 45.7% |
| `apply` | 33.2% | 13.4% | 12.8% | 13.6% | — | 22.4% |
| `intro` | 16.7% | 14.2% | 13.2% | 19.9% | — | 19.9% |
| `intros` | 55.1% | 0.6% | 0.8% | 0.8% | — | 0.1% |
| `induction` | 42.7% | 1.2% | 19.0% | 5.0% | — | 2.4% |
| `cases` | 37.6% | 1.3% | 9.2% | 2.6% | — | 2.0% |
| `ext` | 0.8% | 9.2% | 5.7% | 8.9% | — | 3.5% |
| `ring` | 0.0% | 5.4% | 0.1% | 4.8% | — | 6.6% |
| `norm_num` | 0.0% | 1.8% | 0.0% | 3.5% | — | 8.3% |
| `omega` | 7.4% | 2.1% | 1.4% | 15.0% | — | 4.5% |
| `fun_prop` | 0.0% | 6.4% | 0.2% | 0.0% | — | 0.9% |
| `aesop` | 0.0% | 1.7% | 0.3% | 13.0% | — | 0.3% |

## LeanPool 내부 분포

`LeanPool/<경로 그룹>/`별 추출 정리 수 상위 10개다. 증명의 의미적 중복을 제거한 수가 아니다.

| 경로 그룹 | 추출 정리 | LeanPool 추출 정리 대비 |
| --- | ---: | ---: |
| ConwaySoifer | 39,948 | 10.9% |
| NavierStokesAndEuler | 35,922 | 9.8% |
| MovingSofa | 32,362 | 8.8% |
| NFWeakPartition | 22,603 | 6.2% |
| Zeta5Irrational | 14,969 | 4.1% |
| HopfProblem | 14,945 | 4.1% |
| DavisKahan | 10,004 | 2.7% |
| BeyondBethe | 9,626 | 2.6% |
| BrillNoetherGraphs | 8,325 | 2.3% |
| CaffarelliKohnNirenberg | 8,294 | 2.3% |

## 기준 환경과 한계

- **strata**: `451e5f047bafa010d178856db76c00029bfa4d7f`, `leanprover/lean4:v4.26.0`. 추출 방식: `{'native_lean_ast': 615}`.
- **physlib**: `c48433678e8fb6306ebcd48453300c8e16058a62`, `leanprover/lean4:v4.32.0`. 추출 방식: `{'native_lean_ast': 6755, 'layout_with_native_start_anchor': 2253}`.
- **cslib**: `197a7be621263b84c67ca4f803f69205b36d06df`, `leanprover/lean4:v4.32.0`. 추출 방식: `{'lexical_layout': 1692}`.
- **arklib**: `c1712f6c496d0aef04f09bae42aec13811b3273f`, `leanprover/lean4:v4.31.0`. 추출 방식: `{'lexical_layout': 2686}`.
- **putnambench**: `a635813f5edf297d928f9bd5ef8324a26bdde09c`, `leanprover/lean4:v4.33.1`. 추출 방식: `{'lexical_layout': 672}`.
- **leanpool**: `01db1d7049cf9668bda1e9e106875ee1278b43e6`, `leanprover/lean4:v4.35.0-rc3`. 추출 방식: `{'lexical_layout': 367429, 'reviewed_source_span_override': 19}`.

- CSLib·ArkLib은 Arena warm-up 공통 소스 커밋이다. PutnamBench·LeanPool은 2026-10-14 수집 시 HEAD를 고정했다. PutnamBench warm-up의 version_info 커밋은 Mathlib 환경이며 원본 문제집의 커밋이 아니다.
- 새 네 출처는 lexical/layout 추출이다. 네이티브 AST나 컴파일 검증이 아니며, 미분리 항목은 각 코퍼스 ledger에 남긴다. 파싱 실패 파일 수 등은 각 manifest를 확인한다.
- 추출기의 기존 네이티브 증명 범위 교차검사 기록은 [native_calibration.json](../remaining_sources/native_calibration.json)에 보존했다. 이는 새 출처 전체의 문법 검증을 대신하지 않는다.
- 이름 있는 theorem/lemma만 대상으로 하므로 def/instance/example와 매크로 생성 정리는 포함하지 않는다. 반복·생성 코드와 복제된 증명이 통계를 키울 수 있으며 의미적으로 중복 제거하지 않았다.
- allowlist 밖 custom tactic, syntax quotation, term/tactic 문맥 구별에는 한계가 있다. `<;>` 뒤 tactic은 소스에 적힌 횟수만 센다. 빈도가 비용을 뜻하지 않는다.
- `summary.json`에는 전체 / 직접 sorry 제외 / by 형태 통계를 모두 담았다. `declarations.jsonl.gz`는 선언별 빈도다. 기존 두 출처 비교 보고서는 그대로 보존했다.

```bash
source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent-LeanRefactorArena
python3 scripts/compare_all_sources.py
```
