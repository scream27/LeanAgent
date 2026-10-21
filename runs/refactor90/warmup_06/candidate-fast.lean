lemma ι_timeOrderF_superCommuteF_eq_time {φ ψ : 𝓕.CrAnFieldOp}
    (hφψ : crAnTimeOrderRel φ ψ) (hψφ : crAnTimeOrderRel ψ φ) (a b : 𝓕.FieldOpFreeAlgebra) :
    ι 𝓣ᶠ(a * [ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * b) =
    ι ([ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * 𝓣ᶠ(a * b)) := by
  let p (a b : 𝓕.FieldOpFreeAlgebra) : Prop :=
    ι 𝓣ᶠ(a * [ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * b) =
    ι ([ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * 𝓣ᶠ(a * b))
  change p a b
  refine Submodule.span_induction₂ (R := ℂ) (p := fun a b _ _ => p a b)
    ?_ ?_ ?_ ?_ ?_ ?_ ?_ (Basis.mem_span ofCrAnListFBasis a) (Basis.mem_span ofCrAnListFBasis b)
  · rintro x y ⟨φs', rfl⟩ ⟨φs, rfl⟩
    simp only [p, ofListBasis_eq_ofList, map_mul]
    let l := List.takeWhile (fun c => ¬crAnTimeOrderRel φ c)
      (List.insertionSort crAnTimeOrderRel (φs' ++ φs))
    let m := List.filter (fun c => (crAnTimeOrderRel φ c ∧ crAnTimeOrderRel c φ)) φs'
    let n := List.filter (fun c => (crAnTimeOrderRel φ c ∧ crAnTimeOrderRel c φ)) φs
    let r := List.filter (fun c => (crAnTimeOrderRel φ c ∧ ¬crAnTimeOrderRel c φ))
      (List.insertionSort crAnTimeOrderRel (φs' ++ φs))
    let P (xs : List 𝓕.CrAnFieldOp) := ι (ofCrAnListF xs)
    have hblock (v w : 𝓕.CrAnFieldOp)
        (hv : ∀ c ∈ [v, w], crAnTimeOrderRel φ c ∧ crAnTimeOrderRel c φ) :
        P (crAnTimeOrderList (φs' ++ v :: w :: φs)) =
          P l * P m * P [v, w] * P n * P r := by
      dsimp only [P]
      rw [crAnTimeOrderList,
        show φs' ++ v :: w :: φs = φs' ++ [v, w] ++ φs by simp,
        insertionSort_of_eq_list 𝓕.crAnTimeOrderRel φ φs' [v, w] φs hv]
      repeat rw [ofCrAnListF_append]
      simp [l, m, n, r]
    have hC : P [φ, ψ] - 𝓢(𝓕.crAnStatistics φ, 𝓕.crAnStatistics ψ) • P [ψ, φ] =
        ι [ofCrAnOpF φ, ofCrAnOpF ψ]ₛF := by
      dsimp only [P]
      symm
      rw [superCommuteF_ofCrAnOpF_ofCrAnOpF, ← ofCrAnListF_singleton,
        ← ofCrAnListF_singleton]
      simp [← ofCrAnListF_append]
    calc _
      /- Split the commutator. -/
      _ = crAnTimeOrderSign (φs' ++ φ :: ψ :: φs) •
        ι (ofCrAnListF (crAnTimeOrderList (φs' ++ φ :: ψ :: φs))) -
          crAnTimeOrderSign (φs' ++ ψ :: φ :: φs) •
        𝓢(𝓕.crAnStatistics φ, 𝓕.crAnStatistics ψ) •
          ι (ofCrAnListF (crAnTimeOrderList (φs' ++ ψ :: φ :: φs))) := by
        conv_lhs =>
          rw [← ofCrAnListF_singleton, ← ofCrAnListF_singleton,
            superCommuteF_ofCrAnListF_ofCrAnListF]
          simp [mul_sub, sub_mul, ← ofCrAnListF_append]
          rw [timeOrderF_ofCrAnListF, timeOrderF_ofCrAnListF]
        simp only [map_smul, sub_right_inj]
        module
      /- Simplify the signs. -/
      _ = crAnTimeOrderSign (φs' ++ φ :: ψ :: φs) •
        (ι (ofCrAnListF (crAnTimeOrderList (φs' ++ φ :: ψ :: φs))) -
        𝓢(𝓕.crAnStatistics φ, 𝓕.crAnStatistics ψ) •
          ι (ofCrAnListF (crAnTimeOrderList (φs' ++ ψ :: φ :: φs)))) := by
        rw [crAnTimeOrderSign_swap_eq_time hφψ hψφ]
        module
      _ = crAnTimeOrderSign (φs' ++ φ :: ψ :: φs) •
          (P l * P m * ι [ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * P n * P r) := by
        change _ • (P _ - _ • P _) = _
        rw [hblock φ ψ (by simp [hφψ, hψφ]), hblock ψ φ (by simp [hφψ, hψφ]), ← hC]
        simp [mul_sub, sub_mul]
    dsimp only [P]
    rw [Subalgebra.mem_center_iff.mp (ι_superCommuteF_ofCrAnOpF_ofCrAnOpF_mem_center φ ψ)]
    repeat rw [mul_assoc]
    rw [← map_mul, ← map_mul, ← map_mul, ← ofCrAnListF_append, ← ofCrAnListF_append,
      ← ofCrAnListF_append]
    have h1 := insertionSort_of_takeWhile_filter 𝓕.crAnTimeOrderRel φ φs' φs
    simp only [l, m, n, r, decide_not, Bool.decide_and, List.append_assoc, List.cons_append] at h1 ⊢
    rw [← h1, ← crAnTimeOrderList]
    by_cases hq : (𝓕 |>ₛ φ) ≠ (𝓕 |>ₛ ψ)
    · simp [ι_superCommuteF_of_diff_statistic hq]
    · rw [crAnTimeOrderSign, Wick.koszulSign_eq_rel_eq_stat _ _ hφψ hψφ (not_not.mp hq).symm,
        ← crAnTimeOrderSign, ← ofCrAnListF_append, timeOrderF_ofCrAnListF]
      simp only [map_smul, Algebra.mul_smul_comm]
  · intro y hy
    simp [p]
  · intro x hx
    simp [p]
  · intro x y z hx hy hz hpx hpy
    simp_all [p, add_mul, mul_add]
  · intro x y z hx hy hz hpx hpy
    simp_all [p, mul_add]
  · intro r x y hx hy hpx
    simp_all [p]
  · intro r x y hx hy hpx
    simp_all [p]
