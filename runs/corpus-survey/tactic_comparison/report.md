# Strata·PhysLib 추출 증명의 tactic 빈도 비교

추출한 `proof` 문자열만 대상으로 같은 정적 카운터를 적용했다. 표는 기존 pilot 카운터에 두 코퍼스에서 확인한 tactic 목록과 projection 오탐 보정을 적용한 **확장 카운터** 기준이다. 기존 baseline도 JSON에 그대로 보존했다. **실제 실행 횟수·heartbeat·성능 통계가 아니다.** `def`, `instance`, `example` 및 라이브러리 전체 코드는 분모에 포함하지 않았다.

| 대상 | 추출 정리 | 정리가 있는 파일 | by 증명 | 항 증명 | 패턴 방정식 | 구조 증명 | 직접 sorry 제외 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| strata | 615 | 44 | 589 | 23 | 3 | 0 | 606 |
| physlib | 9,008 | 565 | 7,226 | 1,609 | 95 | 78 | 8,991 |

## 먼저 보이는 차이

- Strata는 `simp_all`(54.5%)·`induction`(42.4%)·`cases`(38.0%)가 많은 정리에 등장한다. PhysLib의 같은 출현률은 각각 5.4%·1.2%·1.3%다.
- PhysLib는 `rw`(44.4%)·`ext`(9.2%)·`fun_prop`(6.4%)가 상대적으로 두드러진다. Strata는 각각 15.4%·0.8%·0%다.
- `simp` 등장 중 `only` 형태는 Strata 59/1,155회(5.1%), PhysLib 4,214/10,647회(39.6%)다. 이는 사용 형태의 차이이며 비용 차이를 의미하지 않는다.

## 주요 tactic 후보

각 셀은 **소스 등장 횟수 / 사용 정리 수 (전체 정리 대비 출현률)**다. 한 정리에서 같은 tactic을 여러 번 쓰면 등장 횟수는 늘지만 사용 정리 수는 한 번만 센다. `<;>`로 여러 목표에 실행되어도 소스에 한 번 쓰였으면 한 번이다. 크기가 다른 코퍼스는 출현률로 비교한다.

`have`, `show`, `calc`, `rfl` 등 term 겸용 head와 `case`·`next` branch 구조, `conv` 계열 제어 head는 아래 별도 표로 옮겼다.

| 후보 head | Strata 횟수 / 정리 (%) | PhysLib 횟수 / 정리 (%) |
| --- | ---: | ---: |
| `simp` | 1,155 / 425 (69.1%) | 10,647 / 4,828 (53.6%) |
| `intros` | 574 / 341 (55.4%) | 63 / 58 (0.6%) |
| `simp_all` | 875 / 335 (54.5%) | 1,039 / 484 (5.4%) |
| `rw` | 207 / 95 (15.4%) | 9,154 / 4,002 (44.4%) |
| `induction` | 281 / 261 (42.4%) | 118 / 109 (1.2%) |
| `cases` | 568 / 234 (38.0%) | 171 / 118 (1.3%) |
| `exact` | 339 / 218 (35.4%) | 4,634 / 2,390 (26.5%) |
| `apply` | 613 / 205 (33.3%) | 2,190 / 1,201 (13.3%) |
| `split` | 364 / 169 (27.5%) | 98 / 65 (0.7%) |
| `assumption` | 288 / 127 (20.7%) | 31 / 15 (0.2%) |
| `intro` | 147 / 103 (16.7%) | 2,406 / 1,279 (14.2%) |
| `constructor` | 168 / 80 (13.0%) | 303 / 273 (3.0%) |
| `refine` | 54 / 38 (6.2%) | 1,289 / 847 (9.4%) |
| `ext` | 5 / 5 (0.8%) | 980 / 827 (9.2%) |
| `simpa` | 0 / 0 (0%) | 1,479 / 713 (7.9%) |
| `obtain` | 19 / 16 (2.6%) | 1,142 / 630 (7.0%) |
| `fun_prop` | 0 / 0 (0%) | 1,060 / 574 (6.4%) |
| `congr` | 2 / 2 (0.3%) | 777 / 522 (5.8%) |

## term 겸용 표기와 branch 구조

이 표는 tactic과 term을 의미적으로 구별하지 않은 문자열 후보다. 예를 들어 `:= rfl`도 카운터가 감지한다. 합계를 순수 tactic 횟수로 해석하면 안 된다.

| head | 분류 | Strata 횟수 / 정리 (%) | PhysLib 횟수 / 정리 (%) |
| --- | --- | ---: | ---: |
| `calc` | term_or_tactic | 0 / 0 (0%) | 246 / 182 (2.0%) |
| `case` | branch_structure | 557 / 211 (34.3%) | 59 / 18 (0.2%) |
| `congrArg` | term_or_tactic | 2 / 2 (0.3%) | 62 / 54 (0.6%) |
| `conv` | conv_control | 1 / 1 (0.2%) | 101 / 58 (0.6%) |
| `conv_lhs` | conv_control | 0 / 0 (0%) | 341 / 226 (2.5%) |
| `conv_rhs` | conv_control | 0 / 0 (0%) | 164 / 123 (1.4%) |
| `decide` | term_or_tactic | 3 / 1 (0.2%) | 178 / 130 (1.4%) |
| `enter` | conv_control | 0 / 0 (0%) | 383 / 212 (2.4%) |
| `funext` | term_or_tactic | 6 / 6 (1.0%) | 627 / 467 (5.2%) |
| `have` | term_or_tactic | 553 / 221 (35.9%) | 5,784 / 1,824 (20.2%) |
| `haveI` | term_or_tactic | 0 / 0 (0%) | 39 / 33 (0.4%) |
| `let` | term_or_tactic | 1 / 1 (0.2%) | 574 / 307 (3.4%) |
| `letI` | term_or_tactic | 0 / 0 (0%) | 45 / 22 (0.2%) |
| `next` | branch_structure | 154 / 80 (13.0%) | 18 / 7 (0.1%) |
| `refl` | term_or_tactic | 0 / 0 (0%) | 2 / 2 (0.0%) |
| `replace` | term_or_tactic | 0 / 0 (0%) | 104 / 74 (0.8%) |
| `rfl` | term_or_tactic | 34 / 26 (4.2%) | 1,813 / 1,650 (18.3%) |
| `set` | term_or_tactic | 0 / 0 (0%) | 153 / 90 (1.0%) |
| `show` | term_or_tactic | 0 / 0 (0%) | 268 / 183 (2.0%) |
| `solve` | tactic_wrapper | 3 / 3 (0.5%) | 0 / 0 (0%) |
| `suffices` | term_or_tactic | 2 / 2 (0.3%) | 132 / 96 (1.1%) |
| `with_unfolding_all` | tactic_wrapper | 0 / 0 (0%) | 57 / 38 (0.4%) |

term/tactic 겸용 문법 전체를 완전하게 셈한 표는 아니다. `conv` 블록 안의 `rw`, `simp` 등도 같은 이름으로 세며, `enter`는 conv 제어 후보로 별도 구분했다.

## simp 형태

| 형태 | Strata 횟수 / 정리 (%) | PhysLib 횟수 / 정리 (%) |
| --- | ---: | ---: |
| `simp only` | 59 / 35 (5.7%) | 4,214 / 2,317 (25.7%) |
| `simp other` | 1,096 / 412 (67.0%) | 6,433 / 3,590 (39.9%) |

`simp_all`, `simpa`, `dsimp`은 `simp`와 합치지 않았다. 두 simp 형태를 한 정리에서 모두 쓰면 사용 정리 수는 서로 겹칠 수 있다. 확장판은 `simp +contextual only`, `simp (disch := fun_prop) only`처럼 옵션 뒤에 있는 `only`도 인식한다. 기존 baseline은 즉시 뒤의 `only`만 인식하며 JSON에 보존했다.

## 표본 선택에 따른 출현률

각 열은 해당 하위집합 전체를 분모로 사용한다. `native_ast`/`layout_recovered`는 선언 경계 추출 방법이며 tactic AST 검증을 뜻하지 않는다. 직접 sorry 제외와 커널 검증은 서로 다른 조건이다.

| 출처·하위집합 | 분모 | simp | rw | apply | exact | simp_all |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| strata / all | 615 | 69.1% | 15.4% | 33.3% | 35.4% | 54.5% |
| strata / no_direct_sorry | 606 | 69.1% | 15.7% | 33.2% | 35.6% | 54.5% |
| strata / by_style | 589 | 71.8% | 15.8% | 34.8% | 36.8% | 56.9% |
| strata / native_ast | 615 | 69.1% | 15.4% | 33.3% | 35.4% | 54.5% |
| strata / kernel_verified_strata | 601 | 69.1% | 15.6% | 32.9% | 35.4% | 54.4% |
| physlib / all | 9,008 | 53.6% | 44.4% | 13.3% | 26.5% | 5.4% |
| physlib / no_direct_sorry | 8,991 | 53.7% | 44.5% | 13.4% | 26.6% | 5.4% |
| physlib / native_ast | 6,755 | 51.2% | 39.4% | 12.0% | 25.6% | 5.0% |
| physlib / by_style | 7,226 | 63.7% | 53.3% | 15.7% | 31.7% | 6.3% |
| physlib / layout_recovered | 2,253 | 60.8% | 59.5% | 17.3% | 29.2% | 6.5% |

## 정리 단위 동시 출현

두 후보가 같은 증명에 등장한 정리 수다. 실행 순서·의존 관계는 알 수 없다. term 겸용 및 branch 구조는 이 표에서 제외했다.

| 출처 | 후보 쌍 | 정리 수 | 해당 코퍼스 비율 |
| --- | --- | ---: | ---: |
| strata | `intros` + `simp` | 249 | 40.5% |
| strata | `simp` + `simp_all` | 242 | 39.3% |
| strata | `intros` + `simp_all` | 206 | 33.5% |
| strata | `induction` + `simp_all` | 200 | 32.5% |
| strata | `induction` + `simp` | 199 | 32.4% |
| physlib | `rw` + `simp` | 2,629 | 29.2% |
| physlib | `exact` + `rw` | 1,510 | 16.8% |
| physlib | `exact` + `simp` | 1,352 | 15.0% |
| physlib | `intro` + `simp` | 938 | 10.4% |
| physlib | `intro` + `rw` | 932 | 10.3% |

## 해석 범위와 재현

- 기존 `scripts/survey.py::tactic_heads` baseline과 확장 카운터를 각각 두 코퍼스에 동일하게 적용했다. 주석·문자열은 제외하며, 줄 시작과 `by`, `<;>`, `;`, `=>` 등의 뒤에서 allowlist에 있는 head를 찾는다. 확장판은 `fun_prop`, `fin_cases`, `erw` 등 관찰된 후보를 추가하고 `(term).right`와 같은 projection 오탐을 보정했다.
- 실제 Lean tactic AST가 아니다. term 구문이나 syntax quotation이 섞이면 오탐할 수 있고, allowlist에 없는 사용자 정의 tactic·새 tactic·일부 modifier 변형은 누락된다. 기존 `try`, `repeat` 등 combinator는 세지 않으며, 확장판 `with_unfolding_all`·`solve`는 wrapper로 별도 표시한다. JSON의 전체 head 합계에는 이러한 구분된 후보도 포함된다.
- `by_style`도 내부 term이 있을 수 있어 순수 tactic AST 통계가 아니다. 감지된 head가 0개인 증명도 분모에서 제외하지 않는다.
- PhysLib는 6,755개 native AST 추출과 2,253개 layout 복원 증명을 함께 포함한다. PhysLib 커널·공리 검증은 미실시이며, Strata 검증 601개는 별도 하위집합으로 제공한다.
- 빈도가 높은 tactic이 느리다는 뜻은 아니다. heartbeat 비용, 최적화 우선순위, 실행 중 목표 수는 이후 별도 측정해야 한다.
- `summary.json`의 `subsets`는 확장판, `baseline_subsets`는 기존판 전체 head와 하위집합·동시출현 통계다. `declarations.jsonl`은 선언별 두 카운터의 head·확장판 증명 상대 줄 번호·원문 링크를 제공한다. 입력·스크립트 SHA-256과 allowlist는 summary에 기록했다.

```bash
source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent-LeanRefactorArena
python3 scripts/compare_tactics.py
PYTHONPATH=scripts python3 -m unittest discover -s tests -p test_compare_tactics.py -v
```
