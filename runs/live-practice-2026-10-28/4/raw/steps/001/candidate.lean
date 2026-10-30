lemma ι_timeOrderF_superCommuteF_superCommuteF_eq_time_ofCrAnListF {φ1 φ2 φ3 : 𝓕.CrAnFieldOp}
    (φs1 φs2 : List 𝓕.CrAnFieldOp) (h :
      crAnTimeOrderRel φ1 φ2 ∧ crAnTimeOrderRel φ1 φ3 ∧
      crAnTimeOrderRel φ2 φ1 ∧ crAnTimeOrderRel φ2 φ3 ∧
      crAnTimeOrderRel φ3 φ1 ∧ crAnTimeOrderRel φ3 φ2) :
    ι 𝓣ᶠ(ofCrAnListF φs1 * [ofCrAnOpF φ1, [ofCrAnOpF φ2, ofCrAnOpF φ3]ₛF]ₛF *
    ofCrAnListF φs2) = 0 := by
  calc _
      _ = ι (𝓣ᶠ(ofCrAnListF (φs1 ++ φ1 :: φ2 :: φ3 :: φs2))) -
          𝓢(𝓕.crAnStatistics φ1, (ofList 𝓕.crAnStatistics [φ2, φ3])) •
          ι (𝓣ᶠ(ofCrAnListF (φs1 ++ φ2 :: φ3 :: φ1 :: φs2))) -
          𝓢(𝓕.crAnStatistics φ2, 𝓕.crAnStatistics φ3) •
          (ι (𝓣ᶠ(ofCrAnListF (φs1 ++ φ1 :: φ3 :: φ2 :: φs2))) -
          𝓢(𝓕.crAnStatistics φ1, ofList 𝓕.crAnStatistics [φ3, φ2]) •
          ι 𝓣ᶠ(ofCrAnListF (φs1 ++ φ3 :: φ2 :: φ1 :: φs2))) := by
        rw [← ofCrAnListF_singleton, ← ofCrAnListF_singleton, ← ofCrAnListF_singleton]
        rw [superCommuteF_ofCrAnListF_ofCrAnListF]
        simp only [List.singleton_append, ofList_singleton, map_sub, map_smul]
        rw [superCommuteF_ofCrAnListF_ofCrAnListF, superCommuteF_ofCrAnListF_ofCrAnListF]
        simp only [List.cons_append, List.nil_append, ofList_singleton, mul_sub, ←
          ofCrAnListF_append, Algebra.mul_smul_comm, sub_mul, List.append_assoc,
          Algebra.smul_mul_assoc, map_sub, map_smul]
  let l1 :=
    (List.takeWhile (fun c => ¬ crAnTimeOrderRel φ1 c)
    ((φs1 ++ φs2).insertionSort crAnTimeOrderRel))
    ++ (List.filter (fun c => crAnTimeOrderRel φ1 c ∧ crAnTimeOrderRel c φ1) φs1)
  let l2 := (List.filter (fun c => crAnTimeOrderRel φ1 c ∧ crAnTimeOrderRel c φ1) φs2)
    ++ (List.filter (fun c => crAnTimeOrderRel φ1 c ∧ ¬ crAnTimeOrderRel c φ1)
    ((φs1 ++ φs2).insertionSort crAnTimeOrderRel))
  have h123 : ι 𝓣ᶠ(ofCrAnListF (φs1 ++ φ1 :: φ2 :: φ3 :: φs2)) =
      crAnTimeOrderSign (φs1 ++ φ1 :: φ2 :: φ3 :: φs2)
      • (ι (ofCrAnListF l1) * ι (ofCrAnListF [φ1, φ2, φ3]) * ι (ofCrAnListF l2)) := by
    have h1 := insertionSort_of_eq_list 𝓕.crAnTimeOrderRel φ1 φs1 [φ1, φ2, φ3] φs2
      (by simp_all)
    rw [timeOrderF_ofCrAnListF, show φs1 ++ φ1 :: φ2 :: φ3 :: φs2 = φs1 ++ [φ1, φ2, φ3] ++ φs2
      by simp, crAnTimeOrderList, h1]
    simp only [List.append_assoc, decide_not,
      Bool.decide_and, ofCrAnListF_append, map_smul, map_mul, l1, l2, mul_assoc]
  have h132 : ι 𝓣ᶠ(ofCrAnListF (φs1 ++ φ1 :: φ3 :: φ2 :: φs2)) =
      crAnTimeOrderSign (φs1 ++ φ1 :: φ2 :: φ3 :: φs2)
      • (ι (ofCrAnListF l1) * ι (ofCrAnListF [φ1, φ3, φ2]) * ι (ofCrAnListF l2)) := by
    have h1 := insertionSort_of_eq_list 𝓕.crAnTimeOrderRel φ1 φs1 [φ1, φ3, φ2] φs2
        (by simp_all)
    rw [timeOrderF_ofCrAnListF, show φs1 ++ φ1 :: φ3 :: φ2 :: φs2 = φs1 ++ [φ1, φ3, φ2] ++ φs2
      by simp, crAnTimeOrderList, h1]
    simp only [decide_not,
      Bool.decide_and, ofCrAnListF_append, map_smul, map_mul, l1, l2, mul_assoc]
    congr 1
    have hp : List.Perm [φ1, φ3, φ2] [φ1, φ2, φ3] := .cons φ1 (.swap φ2 φ3 [])
    rw [crAnTimeOrderSign, Wick.koszulSign_perm_eq _ _ φ1 _ _ _ _ _ hp, ← crAnTimeOrderSign]
    · simp
    · simp_all
  have hp231 : List.Perm [φ2, φ3, φ1] [φ1, φ2, φ3] :=
    ((List.Perm.swap φ1 φ3 []).cons φ2).trans (List.Perm.swap φ1 φ2 [φ3])
  have h231 : ι 𝓣ᶠ(ofCrAnListF (φs1 ++ φ2 :: φ3 :: φ1 :: φs2)) =
      crAnTimeOrderSign (φs1 ++ φ1 :: φ2 :: φ3 :: φs2)
      • (ι (ofCrAnListF l1) * ι (ofCrAnListF [φ2, φ3, φ1]) * ι (ofCrAnListF l2)) := by
    have h1 := insertionSort_of_eq_list 𝓕.crAnTimeOrderRel φ1 φs1 [φ2, φ3, φ1] φs2
        (by simp_all)
    rw [timeOrderF_ofCrAnListF, show φs1 ++ φ2 :: φ3 :: φ1 :: φs2 = φs1 ++ [φ2, φ3, φ1] ++ φs2
      by simp, crAnTimeOrderList, h1]
    simp only [decide_not,
      Bool.decide_and, ofCrAnListF_append, map_smul, map_mul, l1, l2, mul_assoc]
    congr 1
    rw [crAnTimeOrderSign, Wick.koszulSign_perm_eq _ _ φ1 _ _ _ _ _ hp231, ← crAnTimeOrderSign]
    · simp
    · simp_all
  have h321 : ι 𝓣ᶠ(ofCrAnListF (φs1 ++ φ3 :: φ2 :: φ1 :: φs2)) =
      crAnTimeOrderSign (φs1 ++ φ1 :: φ2 :: φ3 :: φs2)
      • (ι (ofCrAnListF l1) * ι (ofCrAnListF [φ3, φ2, φ1]) * ι (ofCrAnListF l2)) := by
    have h1 := insertionSort_of_eq_list 𝓕.crAnTimeOrderRel φ1 φs1 [φ3, φ2, φ1] φs2
        (by simp_all)
    rw [timeOrderF_ofCrAnListF, show φs1 ++ φ3 :: φ2 :: φ1 :: φs2 = φs1 ++ [φ3, φ2, φ1] ++ φs2
      by simp, crAnTimeOrderList, h1]
    simp only [decide_not,
      Bool.decide_and, ofCrAnListF_append, map_smul, map_mul, l1, l2, mul_assoc]
    congr 1
    have hp : List.Perm [φ3, φ2, φ1] [φ1, φ2, φ3] := (List.Perm.swap φ2 φ3 [φ1]).trans hp231
    rw [crAnTimeOrderSign, Wick.koszulSign_perm_eq _ _ φ1 _ _ _ _ _ hp, ← crAnTimeOrderSign]
    · simp
    · simp_all
  rw [h123, h132, h231, h321]
  trans crAnTimeOrderSign (φs1 ++ φ1 :: φ2 :: φ3 :: φs2) • (ι (ofCrAnListF l1) *
    ι [ofCrAnOpF φ1, [ofCrAnOpF φ2, ofCrAnOpF φ3]ₛF]ₛF *
    ι (ofCrAnListF l2)); swap
  · simp
  rw [mul_assoc, ← ofCrAnListF_singleton, ← ofCrAnListF_singleton, ← ofCrAnListF_singleton,
    superCommuteF_ofCrAnListF_ofCrAnListF]
  simp only [List.singleton_append, ofList_singleton, map_sub, map_smul]
  rw [superCommuteF_ofCrAnListF_ofCrAnListF, superCommuteF_ofCrAnListF_ofCrAnListF]
  simp only [List.cons_append, List.nil_append, ofList_singleton, map_sub,
    map_smul, mul_sub, sub_mul, Semigroup.mul_assoc]
  module
