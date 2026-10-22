lemma ι_timeOrderF_superCommuteF_eq_time {φ ψ : 𝓕.CrAnFieldOp}
    (hφψ : crAnTimeOrderRel φ ψ) (hψφ : crAnTimeOrderRel ψ φ) (a b : 𝓕.FieldOpFreeAlgebra) :
    ι 𝓣ᶠ(a * [ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * b) =
    ι ([ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * 𝓣ᶠ(a * b)) := by
  induction ofCrAnListFBasis.mem_span a, ofCrAnListFBasis.mem_span b
    using Submodule.span_induction₂
  case mem_mem hx hy =>
    rcases hx with ⟨φs', rfl⟩
    rcases hy with ⟨φs, rfl⟩
    simp only [ofListBasis_eq_ofList, map_mul]
    let l := List.takeWhile (fun c => ¬crAnTimeOrderRel φ c)
      (List.insertionSort crAnTimeOrderRel (φs' ++ φs)) ++
      List.filter (fun c => crAnTimeOrderRel φ c ∧ crAnTimeOrderRel c φ) φs'
    let r := List.filter (fun c => crAnTimeOrderRel φ c ∧ crAnTimeOrderRel c φ) φs ++
      List.filter (fun c => crAnTimeOrderRel φ c ∧ ¬crAnTimeOrderRel c φ)
        (List.insertionSort crAnTimeOrderRel (φs' ++ φs))
    let P (xs : List 𝓕.CrAnFieldOp) := ι (ofCrAnListF xs)
    have hblock (v w : 𝓕.CrAnFieldOp)
        (hv : ∀ c ∈ [v, w], crAnTimeOrderRel φ c ∧ crAnTimeOrderRel c φ) :
        P (crAnTimeOrderList (φs' ++ v :: w :: φs)) =
          P l * P [v, w] * P r := by
      erw [crAnTimeOrderList,
        ← List.append_assoc φs' [v, w] φs,
        insertionSort_of_eq_list 𝓕.crAnTimeOrderRel φ φs' [v, w] φs hv]
      simp only [P, ofCrAnListF_append, map_mul, l, r, mul_assoc]
    calc
      _ = crAnTimeOrderSign (φs' ++ φ :: ψ :: φs) •
        (P (crAnTimeOrderList (φs' ++ φ :: ψ :: φs)) -
        𝓢(𝓕.crAnStatistics φ, 𝓕.crAnStatistics ψ) •
          P (crAnTimeOrderList (φs' ++ ψ :: φ :: φs))) := by
        conv_lhs =>
          rw [← ofCrAnListF_singleton, ← ofCrAnListF_singleton,
            superCommuteF_ofCrAnListF_ofCrAnListF]
          simp only [List.cons_append, List.nil_append, ofList_singleton, mul_sub, ← ofCrAnListF_append, Algebra.mul_smul_comm, sub_mul, List.append_assoc, Algebra.smul_mul_assoc, map_sub, map_smul]
          rw [timeOrderF_ofCrAnListF, timeOrderF_ofCrAnListF]
        rw [crAnTimeOrderSign_swap_eq_time hφψ hψφ]
        simp only [P, map_smul, smul_sub, sub_right_inj]
        exact smul_comm _ _ _
      _ = _ •
          (P l * ι [ofCrAnOpF φ, ofCrAnOpF ψ]ₛF * P r) := by
        rw [hblock φ ψ (by simp [*]), hblock ψ φ (by simp [*])]
        simp only [P, ofCrAnListF_cons, ofCrAnListF_nil, mul_one,
          superCommuteF_ofCrAnOpF_ofCrAnOpF, map_sub, map_smul, map_mul,
          mul_sub, Algebra.mul_smul_comm, sub_mul, Algebra.smul_mul_assoc]
        rfl
    rw [Subalgebra.mem_center_iff.mp (ι_superCommuteF_ofCrAnOpF_ofCrAnOpF_mem_center φ ψ)]
    simp only [P, mul_assoc]
    rw [← map_mul, ← ofCrAnListF_append]
    dsimp only [l, r]
    rw [← List.append_assoc, ← insertionSort_of_takeWhile_filter 𝓕.crAnTimeOrderRel φ φs' φs, ← crAnTimeOrderList]
    by_cases hq : (𝓕 |>ₛ φ) = (𝓕 |>ₛ ψ)
    · rw [crAnTimeOrderSign, Wick.koszulSign_eq_rel_eq_stat _ _ hφψ hψφ hq.symm,
        ← crAnTimeOrderSign, ← ofCrAnListF_append, timeOrderF_ofCrAnListF]
      simp only [map_smul, Algebra.mul_smul_comm]
    · simp only [ι_superCommuteF_of_diff_statistic hq, zero_mul, smul_zero]
  all_goals
    simp_all only [map_mul, zero_mul, map_zero, mul_zero, add_mul, map_add,
      mul_add, Algebra.smul_mul_assoc, map_smul, Algebra.mul_smul_comm]
