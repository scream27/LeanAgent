# Proof Refactoring Report: Warm-up P7 and P12

**대상 프로젝트:** Cslib, ArkLib  
**참조 소스:** `Cslib/Languages/LambdaCalculus/LocallyNameless/Fsub/Safety.lean`, `ArkLib/Data/CodingTheory/ProximityGap/DG25/MainResults.lean`  
**Lean 버전:** P7 `v4.33.0-rc2`·`v4.32.0`·`v4.31.0`, P12 `v4.31.0`·`v4.30.0`·`v4.29.0`  
**초기 검증 로그:** 2026-10-10  
**추가 평가 기준:** 2026-10-11 17:59:41 KST  
**자료 작성일:** 2026-10-11  

[프레젠테이션용 HTML](presentation.html) — 개념 설명, 단계별 데모, 전후 코드 비교와 검증 결과를 브라우저에서 볼 수 있다.

## Table of Contents

- [Executive Summary](#executive-summary)
- [Overall Metrics Comparison](#overall-metrics-comparison)
- [Evaluation on Three Criteria](#evaluation-on-three-criteria)
- [Problem P7](#problem-p7)
- [Problem P12](#problem-p12)
- [Verification and Axiom Check](#verification-and-axiom-check)

## Executive Summary

P7은 `Typing`이라는 귀납적 정의를 따라 progress를 증명한다. 참조 증명은 합 타입의 두 주입과 두 종류의 추상화를 각각 처리해 같은 논증이 반복됐다. 대칭적인 분기를 합치고 이미 증명된 typing의 well-formedness 결과를 재사용해 정리 전체를 **83줄에서 49줄로 줄였다(41.0%)**.

P12는 interleaved affine-line proximity gap에서 tensor/multilinear correlated agreement를 유도한다. 참조 증명에는 인덱스 복원, cardinality, 형 변환, 확률 부등식 처리가 한 귀납 단계에 섞여 있었다. 사용되지 않는 cardinality 하한을 삭제하고 샘플링 변환·기저 단계·귀납 단계를 보조정리로 분리했다. **주 정리는 177줄에서 17줄로, 새 보조정리를 포함한 비교 범위 전체는 76줄로 줄었다(57.1%)**.

두 문제 모두 JSONL의 `statement`를 그대로 유지했다. 2026-10-10 초기 검증에 이어, 2026-10-11에는 문제별 지정 버전 3개에서 원본·수정본을 각각 검사했다. 총 12회의 파일 검사와 12회의 별도 계측이 모두 성공했고, 수정본의 버전 호환성은 두 문제 모두 **3/3(100%)**다. 공리 목록은 모두 `[propext, Classical.choice, Quot.sound]`로 동일하며 대상 정리의 `sorryAx` 의존성은 없다.

Lean lexer 기준 proof token은 **P7 406 → 301개(25.8621% 감소)**, **P12 1,329 → 745개(43.9428% 감소)**다. P12의 새 보조정리까지 포함한 수치다. Heartbeat는 버전에 따라 P7 **26.7572–27.5751%**, P12 **8.6868–12.6498%** 감소했다. 최신 평가의 수치와 근거는 [evaluation_results.json](metrics.json)에 보존했다.

## Overall Metrics Comparison

| 문제 | 지표 | 원본 | 리팩터링 | 변화 |
| --- | --- | ---: | ---: | --- |
| P7 | 정리 전체 줄 수 | 83 | 49 | 41.0% 감소 |
| P7 | 코드 문자 수 — 공백·주석 제외 | 1,243 | 1,108 | 10.9% 감소 |
| P7 | `grind` 출현 횟수 | 19 | 8 | 57.9% 감소 |
| P7 | 단회 파일 검사 시간 | 4.458초 | 3.517초 | 참고치 |
| P7 | 필요한 공리 | `[propext, Classical.choice, Quot.sound]` | 동일 | 추가 공리 없음 |
| P12 | 주 정리 줄 수 | 177 | 17 | 90.4% 감소 |
| P12 | 새 보조정리 포함 줄 수 | 177 | 76 | 57.1% 감소 |
| P12 | 코드 문자 수 — 공백·주석 제외 | 5,135 | 2,702 | 47.4% 감소 |
| P12 | 단회 파일 검사 시간 | 10.786초 | 10.611초 | 참고치 |
| P12 | 필요한 공리 | `[propext, Classical.choice, Quot.sound]` | 동일 | 추가 공리 없음 |

**집계 범위:** 줄 수는 정리 선언·빈 줄·주석을 포함한다. P12 수정본은 새 보조정리 블록 59줄과 주 정리 17줄의 합이며 두 블록 사이 구분용 빈 줄은 제외한다. 문자 수는 같은 범위에서 공백과 Lean 주석을 제거한 Unicode 문자 수다. import, 공통 문맥, `#check`·`#print axioms`는 제외한다. P12에서 공유하는 앞부분 1,199줄은 변경하지 않았다.

위 시간은 2026-10-10 초기 검증에서 기록한 `lake env lean` 1회 경과 시간으로 의존성 빌드·다운로드는 제외한다. P12는 복원한 공통 보조정리도 매번 검사한다. 이후 별도 계측으로 얻은 Heartbeat는 아래 추가 평가에 기록했다. 경과 시간과 Heartbeat는 측정 범위와 단위가 다르며, 반복 실행에 따른 분산은 측정하지 않았다.

## Evaluation on Three Criteria

**평가 스냅샷:** 2026-10-11 17:59:41 KST. [평가 JSON](metrics.json)의 실제 로컬 실행 결과를 반영했다. 문제별 `version_info`의 고정 커밋·Lean 도구체인을 사용했으며, 공식 Arena worker 점수는 아니다. 아래 감소율은 `100 × (1 − 수정본 / 참조본)`을 소수 넷째 자리까지 계산한 값이다.

### 증명 길이 감소율

| 문제 | 참조 proof token | 수정 proof token | 감소율 |
| --- | ---: | ---: | ---: |
| P7 | 406 | 301 | 25.8621% |
| P12 — 새 보조정리 포함 | 1,329 | 745 | 43.9428% |
| 합계 — 문제별 한 번 집계 | 1,735 | 1,046 | 39.7118% |

사용자가 선택한 **Lean lexer 기준**으로 `Lean.Parser.tokenFn`을 사용했다. 목표 정리의 선언은 제외하고 `by`부터 증명 끝까지 세며, 공백·주석은 제외한다. doc comment는 집계용 입력에서만 일반 주석으로 바꾼다. P12 수정본은 주 증명 **56개**에 새 보조정리의 선언·증명 및 필요한 `omit` 명령 **689개**를 더한 **745개**다. import, 공통 문맥, 검증 명령은 포함하지 않는다.

JSONL에 기록된 `proof_length`는 P7 408, P12 1,353으로, 이번 lexer 집계의 참조값 406·1,329와 다르다. 기존 값은 JSON의 `benchmark_reference_proof_length`로 별도 보존했다. 위 감소율은 원본과 수정본을 같은 lexer로 센 값끼리 계산했으며, 앞 절의 줄 수·문자 수 감소율과도 구분한다. 토큰 수는 각 문제의 세 버전에서 동일했다.

### Heartbeat 감소율

| 문제 | Lean 버전 | 참조 Heartbeat | 수정 Heartbeat | 감소율 | 원본 / 수정본 검사 |
| --- | --- | ---: | ---: | ---: | --- |
| P7 | `v4.33.0-rc2` | 59,804 | 43,313 | 27.5751% | PASS / PASS |
| P7 | `v4.32.0` | 61,942 | 45,358 | 26.7734% | PASS / PASS |
| P7 | `v4.31.0` | 61,916 | 45,349 | 26.7572% | PASS / PASS |
| P12 | `v4.31.0` | 9,167 | 8,112 | 11.5087% | PASS / PASS |
| P12 | `v4.30.0` | 9,178 | 8,017 | 12.6498% | PASS / PASS |
| P12 | `v4.29.0` | 10,257 | 9,366 | 8.6868% | PASS / PASS |

Heartbeat는 Lean elaboration 작업량을 비교하는 지표다. 각 대상 명령의 elaboration 전후 `IO.getNumHeartbeats` 차이를 얻고, **원시값을 합산한 뒤 1,000으로 나눈 정수값**을 표에 기록했다. 참조본은 대상 정리 명령을, 수정본은 대상 정리와 새로 도입한 helper·scope 명령을 측정한다. P12 수정본의 범위는 `helper_scope`, `tensor_success_split`, `tensor_gap_one`, `tensor_gap_succ`, 주 정리의 다섯 명령이다. 원시값은 JSON의 `raw_heartbeats`와 명령별 증거에 보존했다.

import, 공통 보조정리 문맥, 측정 helper 정의, 토큰 계산, `#check`·`#print axioms`는 계측에서 제외했다. 계측 시에만 `Elab.async=false`로 동기 elaboration을 사용했고 기존 `maxHeartbeats` 설정은 유지했다. 버전·변형별로 별도 프로세스에서 한 번 측정했다. 서로 다른 버전의 Heartbeat를 하나로 합산하거나 평균 내지 않았으며, 이 감소율을 파일 전체의 경과 시간 감소율로 해석하지 않는다.

### 버전 호환성

| 문제 | JSONL 지정 버전 | 수정 없이 통과 / 지정 버전 수 | 호환성 |
| --- | --- | ---: | ---: |
| P7 | `v4.33.0-rc2`, `v4.32.0`, `v4.31.0` | 3 / 3 | 100% |
| P12 | `v4.31.0`, `v4.30.0`, `v4.29.0` | 3 / 3 | 100% |
| 합계 | 문제·버전 조합 6개 | 6 / 6 | 100% |

호환성 검사는 계측용 wrapper를 넣지 않은 **바이트 단위로 동일한 원래 파일**로 별도 수행했다. 모든 원본·수정본의 컴파일 종료 코드는 0이며, `-DwarningAsError=true`와 P12의 `-DautoImplicit=false`를 유지했다. 각 버전에서 원본·수정본의 elaborated 타입이 동일하고, 대상 정리의 공리는 `[propext, Classical.choice, Quot.sound]`이며 `sorryAx`는 없다. 지정 버전에 맞추기 위한 증명 코드 변경은 없었다.

| 문제 | Lean 버전 | 고정 라이브러리 커밋 |
| --- | --- | --- |
| P7 | `v4.33.0-rc2` | `3aa9d4416c185e0b9faeb72bbd65abe85b95dbcc` |
| P7 | `v4.32.0` | `197a7be621263b84c67ca4f803f69205b36d06df` |
| P7 | `v4.31.0` | `8ea71c8df91acd63285515a04da952b23b78d266` |
| P12 | `v4.31.0` | `c1712f6c496d0aef04f09bae42aec13811b3273f` |
| P12 | `v4.30.0` | `e6d77b18ca1334a91faf4d1ccf9f96d854d58ba4` |
| P12 | `v4.29.0` | `de71a9dfd2f5a343e8895517b7efe857d9f1ce5c` |

### 평가 근거와 재현

[최종 JSON](metrics.json), 집계 기준 (로컬 설명 자료), 계측 helper (로컬 소스), 평가 스크립트 (로컬 실행 파일), P7 증거 (로컬 검증 기록), P12 증거 (로컬 검증 기록)에 수치·실행 명령·로그·소스 해시를 보존했다. 버전별 증거 폴더에는 수정 없는 검사 파일과 계측 파일을 함께 남겼다. 기존 `P7/result.json`, `P12/result.json`과 초기 로그는 덮어쓰지 않았다.

준비된 환경에서 프로젝트 루트 기준으로 실행한다.

```bash
python3 week2/evaluation/prepare_environments.py
python3 week2/evaluation/run_evaluation.py
```

평가 스크립트는 이미 저장된 버전 결과를 재사용한다. 기존 증거로 최종 JSON만 다시 집계하려면 다음 명령을 사용한다.

```bash
python3 week2/evaluation/run_evaluation.py --aggregate-only
```

## Problem P7

**`Cslib.LambdaCalculus.LocallyNameless.Fsub.Typing.progress`**

### Theorem Statement

```lean
lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t'
```

#### 명제 문법 해설

`lemma Typing.progress`는 `Typing.progress`라는 이름의 정리를 선언한다. 괄호 안의 `(der : Typing [] t τ)`는 정리가 받는 가정이다. `der`는 빈 환경 `[]`에서 항 `t`가 타입 `τ`를 갖는다는 증거이고, 그 뒤의 `:`부터 증명할 결론이 나온다.

`t.Value`는 “t가 값이다”라는 명제다. `∨`는 두 명제 중 하나가 성립한다는 뜻이고, `∃ t', t ⭢βᵛ t'`는 “어떤 다음 항 t'가 존재하며 t가 그 항으로 한 단계 call-by-value 계산된다”는 뜻이다. 결론의 왼쪽을 증명하려면 값이라는 증거를, 오른쪽을 증명하려면 다음 항과 계산 관계의 증거를 함께 제출한다. 이 progress 정리는 한 단계 계산 가능성을 보장하며, 평가가 항상 종료한다는 주장은 아니다.

#### 증명 코드의 흐름

수정본은 먼저 `generalize`로 빈 환경을 `Γ`라는 변수로 바꾸고 그 등식을 남긴다. 전체 typing 증거를 `wholeTyped`로 보존한 뒤 `induction der`로 typing 규칙마다 경우를 나눈다. 각 경우에서 `subst eq`로 빈 환경 조건을 복원하고, 부분항에 대한 귀납가설을 사용한다.

함수 적용에서는 `rcases`로 함수와 인자가 값인지 계산 가능한지 확인한다. 둘 다 값이면 canonical form을 꺼내 `Red.abs`를 사용하고, 인자나 함수가 계산하면 각각 `Red.appᵣ`·`Red.appₗ`로 전체 항의 다음 단계를 만든다. `inl`·`inr`는 같은 코드로 부분항의 결과를 옮긴다. `abs`·`tabs`에서는 `wholeTyped.wf.2.1`로 local closure를 얻어 값임을 보이고, 나머지 규칙도 귀납 결과와 해당 계산 생성자를 연결해 마무리한다.

### Diagnostic and Root Causes

- **대칭적인 분기의 반복:** `inl`과 `inr` 모두 부분항의 값·계산 가능성을 전체 항으로 옮기는 같은 구조를 사용한다.
- **추상화의 local closure 재구성:** `abs`와 `tabs`에서 각각 `LC.abs`, `LC.tabs`를 구성하지만, 이미 `Typing.wf`가 필요한 local closure를 제공한다.
- **계산 규칙의 간접적인 표현:** 함수 적용의 계산 경로가 `exists`와 `grind`에 나뉘어 있어 어떤 계산 생성자를 쓰는지 바로 드러나지 않는다.
- **귀납 문맥의 관리:** 빈 환경을 일반화한 뒤 복원하고, 부분항의 유도와 전체 항의 유도를 구별해야 한다.

### Refactoring Strategy

`Typing` 유도에 대한 귀납법과 빈 환경 일반화는 유지했다. `inl`·`inr`를 하나의 분기로 합쳐 값 생성자와 계산 생성자를 공통 코드로 처리하고, `abs`·`tabs`는 보존한 전체 typing 유도 `wholeTyped`의 `wf.2.1`을 사용한다. 함수 적용은 `Red.abs`, `Red.appᵣ`, `Red.appₗ`을 직접 지정하고 `rcases`로 부분항의 계산 결과를 즉시 분해한다.

### Code Comparison

#### Original Proof — 선언 포함 83줄

원본: `Progress.lean` (로컬 소스). 아래 코드는 JSONL `src` 전체다.

```lean
lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have der' : Typing Γ t τ := der
  induction der <;> subst eq
  case var mem => grind
  case app t₁ _ _ t₂ l r ih_l ih_r =>
    right
    cases ih_l rfl l with
    | inl val_l =>
        cases ih_r rfl r with
        | inl val_r =>
            have ⟨σ, t₁, eq⟩ := l.canonical_form_abs val_l
            exists t₁ ^ᵗᵗ t₂
            grind
        | inr red_r =>
            obtain ⟨t₂', _⟩ := red_r
            exists t₁.app t₂'
            grind
    | inr red_l =>
        obtain ⟨t₁', _⟩ := red_l
        exists t₁'.app t₂
        grind
  case tapp σ' der _ ih =>
    right
    specialize ih rfl der
    cases ih with
    | inl val =>
        obtain ⟨_, t, _⟩ := der.canonical_form_tabs val
        exists t ^ᵗᵞ σ'
        grind
    | inr red =>
        obtain ⟨t', _⟩ := red
        exists .tapp t' σ'
        grind
  case let' t₁ σ t₂ τ L der _ ih _ =>
    right
    cases ih rfl der with
    | inl _ =>
        exists t₂ ^ᵗᵗ t₁
        grind
    | inr red =>
        obtain ⟨t₁', _⟩ := red
        exists t₁'.let' t₂
        grind
  case inl der _ ih =>
    cases (ih rfl der) with
    | inl val => grind
    | inr red =>
        right
        obtain ⟨t', _⟩ := red
        exists .inl t'
        grind
  case inr der _ ih =>
    cases (ih rfl der) with
    | inl val => grind
    | inr red =>
        right
        obtain ⟨t', _⟩ := red
        exists .inr t'
        grind
  case case t₁ _ _ t₂ _ t₃ _ der _ _ ih _ _ =>
    right
    cases ih rfl der with
    | inl val =>
        have ⟨t₁, lr⟩ := der.canonical_form_sum val
        cases lr <;> [exists t₂ ^ᵗᵗ t₁; exists t₃ ^ᵗᵗ t₁] <;> grind
    | inr red =>
        obtain ⟨t₁', _⟩ := red
        exists t₁'.case t₂ t₃
        grind
  case sub => grind
  case abs σ _ τ L _ _=>
    left
    constructor
    apply LC.abs L
    · grind only [→ wf, cases Term.LC]
    · grind only [→ wf]
  case tabs L _ _=>
    left
    constructor
    apply LC.tabs L
    · grind only [→ wf, cases Term.LC]
    · grind only [→ wf]
```

#### Refactored Proof — 선언 포함 49줄

수정본: `ProgressRefactored.lean` (로컬 소스).

```lean
lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  -- Retain the typing derivation to recover local closure after induction.
  have wholeTyped : Typing Γ t τ := der
  induction der <;> subst eq
  case var => grind
  case app t₁ _ _ t₂ leftTyped rightTyped ihLeft ihRight =>
    right
    rcases ihLeft rfl leftTyped with leftValue | ⟨t₁', step⟩
    · rcases ihRight rfl rightTyped with rightValue | ⟨t₂', step⟩
      · obtain ⟨σ, body, rfl⟩ := leftTyped.canonical_form_abs leftValue
        exact ⟨_, Red.abs leftValue.lc rightValue⟩
      · exact ⟨_, Red.appᵣ leftValue step⟩
    · exact ⟨_, Red.appₗ rightTyped.wf.2.1 step⟩
  case tapp σ' typed _ ih =>
    right
    rcases ih rfl typed with value | ⟨t', step⟩
    · obtain ⟨_, body, eq⟩ := typed.canonical_form_tabs value
      exists body ^ᵗᵞ σ'
      grind
    · exists .tapp t' σ'
      grind
  case let' t₁ σ t₂ τ L typed _ ih _ =>
    right
    rcases ih rfl typed with value | ⟨t₁', step⟩
    · exists t₂ ^ᵗᵗ t₁
      grind
    · exists t₁'.let' t₂
      grind
  case inl typed _ ih | inr typed _ ih =>
    -- The two injections share the same value and congruence-step argument.
    rcases ih rfl typed with value | ⟨t', step⟩
    · left
      constructor
      exact value
    · right
      exact ⟨_, by constructor; exact step⟩
  case case t₁ _ _ t₂ _ t₃ _ typed _ _ ih _ _ =>
    right
    rcases ih rfl typed with value | ⟨t₁', step⟩
    · obtain ⟨t₁, side⟩ := typed.canonical_form_sum value
      cases side <;> [exists t₂ ^ᵗᵗ t₁; exists t₃ ^ᵗᵗ t₁] <;> grind
    · exists t₁'.case t₂ t₃
      grind
  case sub => grind
  case abs | tabs =>
    left
    constructor
    exact wholeTyped.wf.2.1
```

### 수정 시도와 결과

| 시도 | 결과·해결 |
| --- | --- |
| 이동한 P7 실행 스크립트의 데이터 경로 확인 | `ROOT / benchmark_data_warmup.jsonl`이 이전 위치를 가리키고 있었다. `ROOT.parent`로 수정한 뒤 참조본 재검증에 성공했다. |
| 전체 typing 유도와 분기별 유도에 같은 `typed` 이름 사용 | `ih rfl typed`에 부분항이 아닌 전체 항의 typing이 전달되는 타입 불일치가 발생했다. 보존한 전체 유도를 `wholeTyped`로 이름 붙여 해결했다. |
| `inl`·`inr`를 합친 분기로 처리 | `case inl ... \| inr ...`에서 값 생성자와 계산 생성자를 같은 코드로 선택하도록 바꿨다. 검증 성공. |
| `abs`·`tabs`의 local closure 구성 통합 | 각자 `LC.abs`·`LC.tabs`를 구성하던 코드를 `wholeTyped.wf.2.1`로 대체했다. 검증 성공. |
| 함수 적용의 계산 규칙 명시 | `Red.abs`, `Red.appᵣ`, `Red.appₗ`로 세 계산 경로를 직접 표현했다. 부분항의 계산 결과는 `rcases`로 즉시 분해한다. 검증 성공. |

### 막힌 점과 남겨 둔 부분

빈 환경 일반화와 전체 typing 유도의 보존은 유지했다. canonical-form 분석과 `let`·`case`의 local closure 조건에는 기존 `grind`를 일부 사용한다. 서로 다른 계산 규칙까지 하나의 큰 자동화 전술로 합치지는 않았다. 최종 증명을 막는 미해결 오류는 없다.

## Problem P12

**`interleaved_affine_gaps_imply_tensor_gaps`**

### Theorem Statement

```lean
theorem interleaved_affine_gaps_imply_tensor_gaps
    (hC_proximityGapAffineLines : e_ε_correlatedAgreementAffineLinesNat
      (F := F) (A := A) (ι := ι) (C := MC) (e := e) (ε := ε))
    (h_interleaved_gaps : ∀ m : ℕ, m ≥ 1 →
      e_ε_correlatedAgreementAffineLinesNat (F := F)
        (A := InterleavedSymbol A (Fin m)) (ι := ι) (C := MC ^⋈ (Fin m)) e ε) :
    ∀ (ϑ : ℕ), (hϑ_gt_0 : ϑ > 0) → δ_ε_multilinearCorrelatedAgreement_Nat (F := F) (A := A)
      (ι := ι) (C := MC) (ϑ := ϑ) (e := e) (ε := ε)
```

#### 명제 문법 해설

`theorem` 다음은 정리의 이름이고, 이어지는 두 괄호는 증명에 필요한 가정이다. `hC_proximityGapAffineLines`는 원래 코드 `MC`의 affine-line gap 성질을 받는다. `h_interleaved_gaps`의 `∀ m : ℕ, m ≥ 1 → …`는 “모든 자연수 m에 대해, m이 1 이상이면 m개 행을 묶은 코드에도 같은 gap 성질이 성립한다”는 뜻이다.

`(F := F)`·`(A := A)`·`(C := MC)`는 정의의 인자를 이름으로 지정하는 문법이다. 여기서 `F`는 스칼라, `A`는 기호의 타입, `ι`는 word의 좌표 타입이다. `Fin m`은 m개 행의 인덱스 타입이고, `InterleavedSymbol A (Fin m)`은 각 열에서 그 행들의 기호를 묶은 타입이다. `MC ^⋈ (Fin m)`는 이에 대응하는 interleaved code를 나타낸다.

두 가정 뒤의 `:`부터 결론이다. `∀ (ϑ : ℕ), (hϑ_gt_0 : ϑ > 0) → …`는 임의의 자연수 차원 `ϑ`와 그 차원이 양수라는 증거를 받아 결론을 보인다는 뜻이다. 마지막의 `δ_ε_multilinearCorrelatedAgreement_Nat`는 해당 차원과 거리·문턱 인자 `e`·`ε`에서의 다중선형 correlated agreement 성질이다.

구체적으로 차원 `ϑ`의 입력은 `2^ϑ`개 행이다. 좌표 벡터 `r`를 균등 샘플링했을 때 다중선형 결합 `M_ϑ(u; r)`이 코드에서 거리 `e` 이내일 확률이 `ϑ · ε / q`보다 크면, 원래 행들의 `jointProximityNat`가 성립한다. 여기서 `q = |F|`이며, 결론은 행을 묶은 word가 interleaved code에서 거리 `e` 이내라는 뜻이다. 여러 행의 불일치를 같은 열 기준으로 센다.

#### 증명 코드의 흐름

주 정리는 `intro ϑ`로 차원을 받은 뒤 `induction ϑ`로 귀납한다. 0차원은 양수 조건과 모순이므로 `omega`로 닫는다. 양의 차원은 다시 나누어, 1차원에서는 `tensor_gap_one`으로 다중선형 결합과 singleton 샘플링을 affine-line 가정에 연결한다. 이때 `Fin 1 → F`의 균등 샘플링을 `F`의 샘플링으로 바꾼다. 2차원 이상에서는 직전 차원의 귀납가설과 interleaved gap 가정을 `tensor_gap_succ`에 넘긴다.

귀납 단계 helper는 입력을 `U₀`·`U₁`로 나누고, `tensor_success_split`의 확률 등식으로 마지막 좌표를 분리한다. 두 절반을 마지막 좌표 `r_last`로 affine 결합한 뒤 남은 좌표 `r_init`로 다중선형 결합하는 재귀식을 사용한다. 그 뒤 좋은 매개변수 집합 `R*`의 확률 하한을 얻고, 귀납가설로 그 집합의 원소마다 interleaved code에 가까움을 보인다. `Pr_le_Pr_of_implies`로 사건 포함을 확률 부등식으로 옮겨 gap 가정을 적용한 다음, `CA_split_rowwise_implies_CA`로 두 절반의 공동 일치를 원래 stack의 결론으로 합친다.

### Diagnostic and Root Causes

- **수동 인덱스 복원:** `Fin.snoc`으로 좌표를 복원하는 과정에서 마지막 인덱스 여부를 분기하고 `omega`와 cast 정규화를 반복한다.
- **불필요한 cardinality 계산:** `h_R_star_card_gt_eps`의 긴 증명 뒤에 그 결과를 사용하는 곳이 없다. 실제 마무리에는 `R*`의 확률 하한과 확률 단조성만 필요하다.
- **형 변환과 부등식의 혼재:** `ℕ`, `ℝ≥0`, `ENNReal` 변환과 분모 소거가 핵심 귀납 논증과 같은 수준에 놓여 있다.
- **인덱스 별칭과 형 주석의 반복:** `ϑ_pred`, `hϑ`, `h_ϑ_pred` 같은 별칭·등식 및 interleaved-word 형 주석이 논증의 흐름을 길게 만든다.

### Refactoring Strategy

사용되지 않는 cardinality 하한과 그 분모 소거·cast 코드를 제거했다. 샘플링 변환을 별도 인터페이스로 묶어 `Fin.snoc`의 수동 재구성을 없애고, 주 정리에서는 귀납 구조가 드러나도록 기저 단계와 귀납 단계를 분리했다.

| 구성 | 역할 |
| --- | --- |
| `tensor_success_split` | 원래 성공 사건과 재귀적인 affine 결합 사건의 점별 동등성을 증명하고, 기존 균등 샘플링 분할 정리를 적용한다. |
| `tensor_gap_one` | singleton 샘플링 변환과 두 행의 표현 변환을 기저 단계 안에 모은다. |
| `tensor_gap_succ` | `R*`의 확률 하한 → 귀납가정으로 얻는 closeness → 사건 포함에 따른 확률 단조성 → interleaved gap을 연결한다. |
| 주 정리 | `0`, `1`, `n+2`의 귀납 구조를 남기고 위 보조정리를 호출한다. |

확률 부등식은 `lt_of_lt_of_le`와 `Pr_le_Pr_of_implies`로 연결한다. 보조정리 추출과 함께 필요 없는 계산을 삭제해, 보조정리를 포함한 전체 비교 범위도 줄였다.

### Code Comparison

#### Original Proof — 선언 포함 177줄

원본: `TensorGaps.lean` (로컬 소스). 아래 코드는 JSONL `src` 전체다.

```lean
theorem interleaved_affine_gaps_imply_tensor_gaps
    (hC_proximityGapAffineLines : e_ε_correlatedAgreementAffineLinesNat
      (F := F) (A := A) (ι := ι) (C := MC) (e := e) (ε := ε))
    (h_interleaved_gaps : ∀ m : ℕ, m ≥ 1 →
      e_ε_correlatedAgreementAffineLinesNat (F := F)
        (A := InterleavedSymbol A (Fin m)) (ι := ι) (C := MC ^⋈ (Fin m)) e ε) :
    ∀ (ϑ : ℕ), (hϑ_gt_0 : ϑ > 0) → δ_ε_multilinearCorrelatedAgreement_Nat (F := F) (A := A)
      (ι := ι) (C := MC) (ϑ := ϑ) (e := e) (ε := ε) := by
    classical
    intro ϑ
    induction ϑ with
    | zero =>
      intro u
      contradiction
    | succ ϑ_sub_1 ih =>
      cases ϑ_sub_1 with
      | zero =>
        -- `ϑ = 1`
        simp only [zero_add, gt_iff_lt, zero_lt_one, ModuleCode, forall_const]
        intro u
        let toAffineLineEval := multilinearCombine₁_eq_affineLineEvaluation (F := F) (u := u)
        intro hprob_gt
        simp_rw [toAffineLineEval] at hprob_gt
        let prob_eq := prob_uniform_singleton_finFun_eq (F := F)
          (P := fun r => Δ₀(affineLineEvaluation (u 0) (u 1) r, MC) ≤ e)
        -- Convert sampling (r ← (Fin 1 → F)) into sampling (r ← F)
        simp_rw [prob_eq, Nat.cast_one, ENNReal.coe_one, one_mul] at hprob_gt
        have h_correlated_agreement := hC_proximityGapAffineLines (u 0) (u 1) hprob_gt
        simp only [jointProximityNat₂, Fin.isValue] at h_correlated_agreement
        have h_u_eq: u = finMapTwoWords (u 0) (u 1) := by
          funext rowIdx
          match rowIdx with
          | 0 => rfl
          | 1 => rfl
        rw [h_u_eq.symm] at h_correlated_agreement
        exact h_correlated_agreement
      | succ ϑ_sub_2 =>
        intro hϑ_gt_0 u hP_multilinearCombine_close_gt
        -- `ϑ ≥ 2`
        -- set ϑ_sub_1 := ϑ_sub_2 + 1
        let ϑ := ϑ_sub_2 + 1 + 1
        have hϑ : ϑ = ϑ_sub_2 + 1 + 1 := by rfl
        -- have hfinϑ : Fin ϑ = Fin (ϑ_sub_2 + 1 + 1) := by rfl
        set U₀ : Fin (2 ^ (ϑ_sub_2 + 1)) → Word A ι :=
          (splitHalfRowWiseInterleavedWords (ϑ := ϑ_sub_2 + 1) u).1
        set U₁ : Fin (2 ^ (ϑ_sub_2 + 1)) → Word A ι :=
          (splitHalfRowWiseInterleavedWords (ϑ := ϑ_sub_2 + 1) u).2
        unfold jointProximityNat
        simp only
        -- intro hP_multilinearCombine_close_gt
        have h_finsnoc_eq_r: ∀ r: Fin (ϑ_sub_2 + 1 + 1) → F,
          Fin.snoc (fun (i : Fin (ϑ_sub_2 + 1)) ↦ r i.castSucc)
            (r (Fin.last (ϑ_sub_2 + 1))) = r := fun r => by
          funext i
          have hi_le_lt := i.isLt
          by_cases h : i = Fin.last (ϑ_sub_2 + 1)
          · simp only [h, Fin.snoc_last]
          · have h_i_ne_last: i ≠ Fin.last (ϑ_sub_2 + 1) := by omega
            have h_i_ne_last_val: i.val ≠ Fin.last (ϑ_sub_2 + 1) := by omega
            rw [Fin.val_last] at h_i_ne_last_val
            have h_i_lt: i.val < (ϑ_sub_2 + 1) := by omega
            simp only [Fin.snoc, Fin.castSucc_castLT, cast_eq, dite_eq_ite, ite_eq_left_iff, not_lt]
            simp only [isEmpty_Prop, not_le, h_i_lt, IsEmpty.forall_iff]
        let P : F → (Fin (ϑ_sub_2 + 1) → F) → Prop := fun r_last r_init =>
          Δ₀(multilinearCombine (u:=u) (r:=Fin.snoc r_init r_last), MC) ≤ e
        let hP_split_r_last := prob_split_last_uniform_sampling_of_finFun
          (ϑ := ϑ_sub_2 + 1) (F := F) (P := P)
        unfold P at hP_split_r_last
        simp_rw [h_finsnoc_eq_r] at hP_split_r_last
        rw [hP_split_r_last] at hP_multilinearCombine_close_gt
        -- Now we have two randomness sampling in hP_multilinearCombine_close_gt :
        -- `((ϑ_sub_2 + 1 + 1) * ε) / |𝔽|
          -- < Pr_{ r_last; r_init }[  Δ₀((Fin.snoc r_init r_last)|⨂|u, ↑MC) ≤ ↑e)) ]` (0)
        -- We need to achieve the upperbound for hP_multilinearCombine_close_gt probability by:
        -- i.e. `Pr_{ r_last; r_init }[  Δ₀((Fin.snoc r_init r_last)|⨂|u, ↑MC) ≤ ↑e)) ]`
        -- `= Pr_{ r_last; r_init }[ Δ₀((r_init)|⨂|affineCombine(U₀, U₁, r_last), ↑MC) ≤ ↑e)) ]`
        -- `= PR_{ r_last }[ r_init; Δ₀((r_init)|⨂|affineCombine(U₀, U₁, r_last), ↑MC) ≤ ↑e)) ]`
        -- Divide into two cases: r_last ∈ R* and r_last ∉ R*
        -- `= Pr_{ r_last }[ r_last ∈ R* ∧
          -- Pr_{ r_init }[ Δ₀((r_init)|⨂|affineCombine(U₀, U₁, r_last), ↑MC) ≤ ↑e)) ]` (1)
        -- `+ Pr_{ r_last }[ r_last ∉ R* ∧
          -- Pr_{ r_init }[ Δ₀((r_init)|⨂|affineCombine(U₀, U₁, r_last), ↑MC) ≤ ↑e)) ]` (2)
        -- `(1) = Pr_{ r_last }[ r_last ∈ R* ]` (3)
        -- `(2): ∀ r ∉ R*, it's trivial that the probability
          -- ≤ ((ϑ_sub_2 + 1) * ε) / |𝔽|, due to definition of membership of R*` (4)

        -- Combine (0), (3), (4): we have `Pr_{ r_last }[ r_last ∈ R* ] > ε/|𝔽|` (5)

        -- Applying `correlatedAgreement_of_mem_R_star_tensor` to (5), we get
          -- `Δ₀((r_last)|⨂|affineCombine(U₀, U₁, r_last), ↑MC) ≤ ↑e)) ] > ε/|𝔽|` (6)
        -- This is premise for affineProxmityGaps of interleaved code (`h_interleaved_gaps`)
          -- for `m = 2^{ϑ_sub_2 + 1}`, which directly leads to Q.E.D.
        let  ϑ_pred := ϑ_sub_2 + 1
        have h_ϑ_pred : ϑ_pred = ϑ_sub_2 + 1 := by rfl
        have h_ϑ : ϑ = ϑ_pred + 1 := by rfl
        -- Step 1: Apply multilinearCombine recursive form
        -- We need the lemma `multilinearCombine u r = multilinearCombine`
          -- `(affineLineEvaluation U₀ U₁ r_last) r_init` where `r = Fin.snoc r_init r_last`
        have multilinearCombine_snoc_eq_multilinearCombine_affine
          (r_init : Fin ϑ_pred → F) (r_last : F) : multilinearCombine u (Fin.snoc r_init r_last) =
            multilinearCombine (affineLineEvaluation U₀ U₁ r_last) r_init := by
          rw [multilinearCombine_recursive_form]
          simp only [Fin.snoc_last, Fin.init_snoc]
          rfl
        -- Rewrite the probability using this identity
        simp_rw [multilinearCombine_snoc_eq_multilinearCombine_affine]
          at hP_multilinearCombine_close_gt
        -- hP_multilinearCombine_close_gt now looks like:
        -- Pr_{ r_last ← $ᵖ F; r_init ← $ᵖ (Fin ϑ_pred → F) }[ Δ₀(multilinearCombine
            -- (affineLineEvaluation U₀ U₁ r_last) r_init, ↑MC) ≤ ↑e ] > ↑(↑ϑ * ↑ε) / q
        -- Step 2 & 3: Define R* and apply Law of Total Probability
        let R_star_set := R_star_tensor MC (m:=ϑ_pred) (e:=e) (ε:=ε) U₀ U₁
        -- Step 5: Show Pr[R*] > ε / q
        have h_prob_Rstar_gt_eps_div_q : Pr_{ let r ← $ᵖ F }[ r ∈ R_star_set ]
          > (↑ε : ENNReal) / (Fintype.card F : ENNReal) := by
          let res := prob_R_star_gt_threshold (MC := MC) (ε := ε) (ϑ := ϑ_sub_2 + 1) (u := u)
            (e := e) (hP_multilinearCombine_close_gt)
          exact res
        -- Convert Pr_{}[] to cardinality
        have h_R_star_card_gt_eps : R_star_set.card > ε := by
          rw [prob_uniform_eq_card_filter_div_card] at h_prob_Rstar_gt_eps_div_q -- Needs NNReal
          simp only [ENNReal.coe_natCast] at h_prob_Rstar_gt_eps_div_q
          rw [gt_iff_lt] at h_prob_Rstar_gt_eps_div_q
          have h_cancel_q_denom := ENNReal.div_lt_div_iff_left
            (a := (ε : ENNReal))
            (b := (#(filter (fun r => r ∈ R_star_set) Finset.univ)))
            (c := (Fintype.card F : ENNReal)) (hc₀ := by simp only [ne_eq,
            Nat.cast_eq_zero, Fintype.card_ne_zero, not_false_eq_true]) (hc := by simp only [ne_eq,
              ENNReal.natCast_ne_top, not_false_eq_true])
          rw [h_cancel_q_denom] at h_prob_Rstar_gt_eps_div_q
          simp only [filter_univ_mem, Nat.cast_lt] at h_prob_Rstar_gt_eps_div_q
          exact h_prob_Rstar_gt_eps_div_q
        -- Step 6: Apply Inductive Hypothesis for r_last ∈ R*
        have h_line_close_to_C_m : ∀ (r : R_star_set),
          jointProximityNat (u := affineLineEvaluation U₀ U₁ r.val) (e := e) (C := MC) := by
          intro r_in_Rstar
          -- Use the lemma proven earlier
          apply correlatedAgreement_of_mem_R_star_tensor
            (ih := fun u_prev => ih (by omega) u_prev ) (u := u)
        -- Step 7: Apply Affine Gap of Interleaved Code C^(m = 2^(ϑ_sub_2 + 1))
        have h_C_m_gap := h_interleaved_gaps (2^(ϑ_sub_2 + 1)) (Nat.one_le_two_pow)
        -- Need the hypothesis Pr[...] > ε/q for h_C_m_gap
        have h_prob_line_gt_eps_div_q :
          Pr_{ let r ← $ᵖ F }[
            Δ₀(affineLineEvaluation (u₀ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₀))
              (u₁ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₁)) (r := r),
              ((MC ^⋈ (Fin (2 ^ (ϑ_sub_2 + 1)))))) ≤ e
          ] > (↑ε : ENNReal) / (Fintype.card F : ENNReal) := by
            -- This is implied by h_prob_Rstar_gt_eps_div_q becuz R* is a subset of the success set
            apply lt_of_le_of_lt' _ h_prob_Rstar_gt_eps_div_q
            have h_r_implies: ∀ (r : F), r ∈ R_star_set →
              Δ₀(affineLineEvaluation
                (u₀ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₀))
                (u₁ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₁)) (r := r),
                ((MC ^⋈ (Fin (2 ^ (ϑ_sub_2 + 1)))))) ≤ e := by
              intro r hr_in_Rstar
              specialize h_line_close_to_C_m ⟨r, hr_in_Rstar⟩
              unfold jointProximityNat at h_line_close_to_C_m
              exact h_line_close_to_C_m
            let Pr_le := Pr_le_Pr_of_implies (D := $ᵖ F)
              (g := fun r => Δ₀(affineLineEvaluation
                (u₀ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₀))
                (u₁ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₁)) (r := r),
                ((MC ^⋈ (Fin (2 ^ (ϑ_sub_2 + 1)))))) ≤ e)
              (f := fun r => r ∈ R_star_set) (h_imp := h_r_implies)
            simp only at Pr_le
            exact Pr_le
        -- Apply the gap property of C^m
        have h_final_gap : jointProximityNat₂
          (u₀ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₀))
          (u₁ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₁)) (e := e)
          (C := (MC ^⋈ (Fin (2^(ϑ_sub_2 + 1))))) := by
          apply h_C_m_gap (u₀ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₀))
            (u₁ := ⋈|(show WordStack A (Fin (2 ^ (ϑ_sub_2 + 1))) ι from U₁))
            (h_prob_line_gt_eps_div_q)
        apply CA_split_rowwise_implies_CA (u := u) (e := e)
        exact h_final_gap
```

#### Refactored Helpers — 59줄

수정본: `TensorGapsRefactored.lean` (로컬 소스). 다음 보조정리와 주 정리를 함께 검증한다.

```lean
-- The helpers below expose the sampling and induction interfaces explicitly.
omit [DecidableEq F] [NoZeroDivisors F] [Fintype A] [Module.Free F A] [Nontrivial ↥MC]

omit [Nonempty ι] [DecidableEq ι] in
/-- Split the last coordinate once, keeping all probability coercions behind an equality. -/
private lemma tensor_success_split {n : ℕ}
    (u : WordStack A (Fin (2 ^ (n + 1))) ι) :
    Pr_{let r ← $ᵖ (Fin (n + 1) → F)}[Δ₀(multilinearCombine u r, MC) ≤ e] =
    Pr_{let r_last ← $ᵖ F; let r_init ← $ᵖ (Fin n → F)}[
      multilinearCombine_affineComb_split_last_close (MC := MC) u e r_last r_init] := by
  classical
  have fold (r : Fin (n + 1) → F) :
      (Δ₀(multilinearCombine u r, MC) ≤ e) =
        multilinearCombine_affineComb_split_last_close (MC := MC) u e
          (r (Fin.last n)) (fun i => r i.castSucc) := by
    unfold multilinearCombine_affineComb_split_last_close
    rw [multilinearCombine_recursive_form]
    rfl
  simp_rw [fold]
  exact prob_split_last_uniform_sampling_of_finFun _

/-- The one-coordinate tensor statement is exactly the affine-line statement. -/
private lemma tensor_gap_one
    (hC : e_ε_correlatedAgreementAffineLinesNat (F := F) (A := A) (ι := ι) (C := MC) e ε) :
    δ_ε_multilinearCorrelatedAgreement_Nat (F := F) (A := A) (ι := ι) (C := MC) 1 e ε := by
  classical
  intro u hprob
  simp_rw [multilinearCombine₁_eq_affineLineEvaluation (F := F) (u := u)] at hprob
  simp_rw [prob_uniform_singleton_finFun_eq (F := F)
    (P := fun r => Δ₀(affineLineEvaluation (u 0) (u 1) r, MC) ≤ e),
    Nat.cast_one, ENNReal.coe_one, one_mul] at hprob
  have hCA := hC (u 0) (u 1) hprob
  have hu : u = finMapTwoWords (u 0) (u 1) := by
    funext i
    fin_cases i <;> rfl
  simpa only [jointProximityNat₂, ← hu] using hCA

/-- Lift the tensor statement by one coordinate via the good-parameter set R*. -/
private lemma tensor_gap_succ {n : ℕ}
    (ih : δ_ε_multilinearCorrelatedAgreement_Nat (F := F) (A := A) (ι := ι) (C := MC) n e ε)
    (hGaps : ∀ m : ℕ, m ≥ 1 → e_ε_correlatedAgreementAffineLinesNat (F := F)
      (A := InterleavedSymbol A (Fin m)) (ι := ι) (C := MC ^⋈ (Fin m)) e ε) :
    δ_ε_multilinearCorrelatedAgreement_Nat (F := F) (A := A) (ι := ι) (C := MC) (n + 1) e ε := by
  classical
  intro u hprob
  let U₀ := (splitHalfRowWiseInterleavedWords (ϑ := n) u).1
  let U₁ := (splitHalfRowWiseInterleavedWords (ϑ := n) u).2
  let good := R_star_tensor MC (m := n) (e := e) (ε := ε) U₀ U₁
  have hgood : Pr_{let r ← $ᵖ F}[r ∈ good] >
      (ε : ENNReal) / (Fintype.card F : ENNReal) := by
    apply prob_R_star_gt_threshold (MC := MC) (u := u) (e := e)
    rwa [← tensor_success_split (MC := MC) (u := u)]
  have hclose : ∀ r : F, r ∈ good →
      Δ₀(affineLineEvaluation (⋈|U₀) (⋈|U₁) r, MC ^⋈ (Fin (2 ^ n))) ≤ e := by
    intro r hr
    exact correlatedAgreement_of_mem_R_star_tensor (MC := MC) (ih := ih) (u := u) ⟨r, hr⟩
  apply CA_split_rowwise_implies_CA (C := MC) (u := u) (e := e)
  apply hGaps (2 ^ n) Nat.one_le_two_pow (⋈|U₀) (⋈|U₁)
  exact lt_of_lt_of_le hgood (Pr_le_Pr_of_implies (D := $ᵖ F) (h_imp := hclose))
```

#### Refactored Main Proof — 선언 포함 17줄

```lean
theorem interleaved_affine_gaps_imply_tensor_gaps
    (hC_proximityGapAffineLines : e_ε_correlatedAgreementAffineLinesNat
      (F := F) (A := A) (ι := ι) (C := MC) (e := e) (ε := ε))
    (h_interleaved_gaps : ∀ m : ℕ, m ≥ 1 →
      e_ε_correlatedAgreementAffineLinesNat (F := F)
        (A := InterleavedSymbol A (Fin m)) (ι := ι) (C := MC ^⋈ (Fin m)) e ε) :
    ∀ (ϑ : ℕ), (hϑ_gt_0 : ϑ > 0) → δ_ε_multilinearCorrelatedAgreement_Nat (F := F) (A := A)
      (ι := ι) (C := MC) (ϑ := ϑ) (e := e) (ε := ε) := by
  intro ϑ
  induction ϑ with
  | zero => intro h; omega
  | succ n ih =>
    cases n with
    | zero => intro _; exact tensor_gap_one (MC := MC) hC_proximityGapAffineLines
    | succ n =>
      intro _
      exact tensor_gap_succ (MC := MC) (ih (Nat.succ_pos n)) h_interleaved_gaps
```

### 수정 시도와 결과

| 시도 | 관찰한 결과 | 해결·다음 시도 |
| --- | --- | --- |
| 1차 (로컬 로그): 보조정리 분리 및 `Fin.snoc_init_self`로 정규화 | `simp made no progress`와 `ModuleCode`→`Set` 인자의 타입 추론 오류 | 보조정리에 `A`, `ι`를 명시하고, `snoc` 재구성을 거치지 않는 샘플링 분할 형태로 변경했다. |
| 2차 (로컬 로그): 샘플링 등식을 `simpa only`로 한꺼번에 정규화 | 확률식 내부의 `Fin.init r`와 `fun i => r i.castSucc`가 맞지 않았다. 기저 단계의 일반적인 singleton 정리 적용도 진행되지 않았다. | 기저 단계의 사건 predicate를 명시했다. |
| 3차 (로컬 로그): `Fin.init`를 simp 목록에 추가 | 기저 단계는 해결됐지만 확률식 내부의 표현 불일치는 남았다. | 전체 확률식을 직접 단순화하는 방식에서 벗어났다. |
| 4차 (로컬 로그): 확률 함수에 `apply congrArg` 적용 | 고차 함수 인자의 단일화가 실패했다. | 각 샘플 `r`에서 사건 자체의 동등성을 먼저 증명하도록 바꿨다. |
| 5차 (로컬 로그): 점별 `fold` 등식과 `simp_rw` 사용 | 재귀식 rewrite 뒤 `Fin.init`와 lambda 사이의 정의적 동등성 목표가 남았다. | 그 작은 목표를 `rfl`로 닫았다. |
| 6차 (로컬 로그): 논리적 증명 완성 | 공리 목록에 `sorryAx`는 없었으나, sampling helper의 불필요한 `[Nonempty ι]`, `[DecidableEq ι]` 가정이 경고를 발생시켜 엄격 검증에 실패했다. | 해당 helper에만 `omit ... in`을 지정했다. 경고 검사를 끄지 않았다. |
| 최종 재실행 | 참조본·수정본 모두 종료 코드 0, 경고 오류 없음, 대상 정리의 `sorryAx` 없음 | 최종 수정본 로그 (로컬 로그)와 결과 JSON (로컬 검증 기록)에 기록했다. |

실패 로그의 줄 번호는 각 시도 당시 파일 기준이다. 컴파일 오류가 있던 시도의 공리 출력은 성공 판정에 사용하지 않았다.

### 막힌 점과 남아 있는 범위

최종 대상 증명의 미해결 오류는 없다. 다만 기존 보조정리 문맥 1,199줄은 여전히 복원해서 사용한다. 이를 라이브러리 모듈로 재편하는 작업까지 수행한 것은 아니다.

ArkLib 의존성 빌드에서는 `ArkLib/Data/Fin/Basic.lean:307`과 `ArkLib/Data/MvPolynomial/Interpolation.lean:258`의 기존 `sorry` 경고가 재출력된다. 해당 라이브러리 전체가 `sorry` 없이 완성됐다는 뜻은 아니다. 이번 대상 정리의 실제 전이적 공리 목록에는 원본·수정본 모두 `sorryAx`가 없으며, 기존 라이브러리의 미완성 부분을 수정하지는 않았다.

## Verification and Axiom Check

### Initial Build Verification (2026-10-10)

프로젝트 루트인 `leanProject`에서 실행한다.

```bash
python3 week2/P7/run_progress.py
python3 week2/P12/run_tensor_gaps.py
```

기본값은 참조본과 수정본을 모두 검증하는 `--variant both`다. 한쪽만 검증하려면 `--variant reference` 또는 `--variant refactored`를 붙인다. `--extract-only`는 JSONL에서 참조본만 다시 생성한다. 수정본은 어떤 모드에서도 덮어쓰지 않는다.

| 문제 | 필요한 import 모듈 빌드 | 참조본 검사 | 수정본 검사 | 최종 기록 |
| --- | --- | --- | --- | --- |
| P7 | `Cslib.Languages.LambdaCalculus.LocallyNameless.Fsub.Typing` 성공 | PASS, 종료 코드 0 | PASS, 종료 코드 0 | 원본 로그 (로컬 로그), 수정 로그 (로컬 로그), `result.json` (로컬 검증 기록) |
| P12 | `ArkLib.Data.CodingTheory.ProximityGap.DG25.Basic` 성공 | PASS, 종료 코드 0 | PASS, 종료 코드 0 | 원본 로그 (로컬 로그), 수정 로그 (로컬 로그), `result.json` (로컬 검증 기록) |

초기 검증은 `P7/cslib-progress`와 `P12/arklib` checkout에서 정의·보조정리·고정 버전 의존성·빌드 결과를 사용했다. 추가 평가에서는 P7 `v4.33.0-rc2`에 기존 `P7/cslib-progress`를, 나머지 다섯 환경에는 `evaluation/envs/`의 별도 고정 checkout을 사용했다. 라이브러리 저장소의 추적 파일은 수정하지 않았다. 검증 범위는 필요한 import 모듈과 두 문제의 참조본·수정본이며 전체 라이브러리 CI 결과는 아니다.

### Reference Reconstruction and Environment

출처는 `benchmark_data_warmup.jsonl` (로컬 원본 데이터)의 7번째와 12번째 항목이다. `header`가 비어 있어 `src`만 독립 실행할 수 없다. 실행 스크립트가 고정 커밋의 소스와 JSONL `src`의 일치를 확인하고 필요한 문맥을 복원한다.

| 문제 | 항목 이름 | Lean | 라이브러리 커밋 |
| --- | --- | --- | --- |
| P7 | `Cslib.LambdaCalculus.LocallyNameless.Fsub.Typing.progress` | `v4.33.0-rc2` | `3aa9d4416c185e0b9faeb72bbd65abe85b95dbcc` |
| P12 | `interleaved_affine_gaps_imply_tensor_gaps` | `v4.31.0` | `c1712f6c496d0aef04f09bae42aec13811b3273f` |

P7은 `Fsub.Typing`만 import하고 namespace·변수를 복원한다. 대상 정리가 이미 들어 있는 `Fsub.Safety`는 import하지 않는다. P12는 `DG25.Basic`을 import하고 `MainResults.lean`에서 대상 정리 앞의 보조정리 문맥을 복원한다. 대상 정리를 포함한 `MainResults` 자체를 import하지 않는다. 따라서 수정본이 참조 정리를 그대로 호출해 증명을 끝내는 구조가 아니다.

2026-10-10 검증 당시 Lean MCP 도구가 세션에 없어 `lake env lean`으로 수정한 파일을 확인했다. 최종 스크립트는 필요한 import 모듈을 `lake build`한 뒤 두 파일을 각각 검사한다. 수정본에도 JSONL의 명제 선언이 그대로 있는지 확인하며, `-DwarningAsError=true`로 대상 파일의 경고를 오류로 처리한다. P12는 원본 환경에 맞춰 `-DautoImplicit=false`도 지정한다.

### Axiom Verification

각 증명 파일 끝에서 다음 명령으로 정리의 타입과 전이적 공리 의존성을 확인했다.

```lean
-- P7
#check Typing.progress
#print axioms Typing.progress

-- P12
#check interleaved_affine_gaps_imply_tensor_gaps
#print axioms interleaved_affine_gaps_imply_tensor_gaps
```

| 대상 | 참조본 공리 목록 | 수정본 공리 목록 | `sorryAx` |
| --- | --- | --- | --- |
| P7 | `[propext, Classical.choice, Quot.sound]` | `[propext, Classical.choice, Quot.sound]` | 없음 |
| P12 | `[propext, Classical.choice, Quot.sound]` | `[propext, Classical.choice, Quot.sound]` | 없음 |

문제별 참조본·수정본의 `#check`·`#print axioms` 출력 전체가 동일함을 확인했다. `Classical.choice`는 원본에도 포함되어 있으며, 리팩터링으로 추가된 공리는 없다. ArkLib 의존성의 기존 `sorry` 경고와 대상 정리의 실제 공리 의존성은 구분했다.

### 실행 스크립트와 결과 파일

두 실행 스크립트는 참조본만 JSONL에서 재생성하고 수정본을 보존한다. 검증할 파일이 원래 명제 선언을 유지하는지 검사하고, 각 변형의 종료 코드·`sorryAx` 여부·경과 시간을 `result.json`에 저장한다. `reference.log`와 `refactored.log`는 가장 최근에 선택해 실행한 변형의 Lean 출력을 저장한다. `result.json`은 가장 최근 실행에서 선택한 변형들만 담으므로, 두 증명의 결과를 함께 갱신하려면 기본 명령 또는 `--variant both`를 사용한다.
