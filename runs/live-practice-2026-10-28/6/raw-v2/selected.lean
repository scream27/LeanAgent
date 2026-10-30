lemma isExtrema_lorentzGroup_apply_iff {𝓕 : FreeSpace}
    (A : ElectromagneticPotential d)
    (hA : ContDiff ℝ ∞ A) (J : LorentzCurrentDensity d) (hJ : ContDiff ℝ ∞ J)
    (Λ : LorentzGroup d) :
    IsExtrema 𝓕 (Λ • A) (fun x => Λ • J (Λ⁻¹ • x)) ↔
    IsExtrema 𝓕 A J := by
  rw [isExtrema_iff_tensors]
  conv_lhs =>
    enter [x, 1, 1, 2, 2, 2]
    change tensorDeriv (fun x => toFieldStrength (Λ • A) x) x
    enter [1,x]
    rw [toFieldStrength_equivariant _ _ (hA.differentiable (by simp))]
  conv_lhs =>
    enter [x]
    rw [tensorDeriv_equivariant _ _ _ (differentiable_toFieldStrength_of_smooth hA),
      smul_comm, Tensorial.toTensor_smul, Tensorial.toTensor_smul]
    simp only [one_div, map_smul, actionT_smul,
      contrT_equivariant, map_neg, permT_equivariant]
    rw [smul_comm, ← Tensor.actionT_neg, ← Tensor.actionT_add]
  apply Iff.intro
  · intro h
    rw [isExtrema_iff_tensors A hA J hJ]
    intro x
    apply MulAction.injective Λ
    simp only [one_div, map_smul, map_neg,
      _root_.smul_add, actionT_smul, _root_.smul_neg, _root_.smul_zero]
    simpa using h (Λ • x)
  · intro h x
    rw [isExtrema_iff_tensors A hA J hJ] at h
    specialize h (Λ⁻¹ • x)
    simp at h
    simp [h]
  · change ContDiff ℝ ∞ (actionCLM Λ ∘ A ∘ actionCLM Λ⁻¹)
    exact (ContinuousLinearMap.contDiff (actionCLM Λ)).comp
      (hA.comp (ContinuousLinearMap.contDiff (actionCLM Λ⁻¹)))
  · change ContDiff ℝ ∞ (actionCLM Λ ∘ J ∘ actionCLM Λ⁻¹)
    exact (ContinuousLinearMap.contDiff (actionCLM Λ)).comp
      (hJ.comp (ContinuousLinearMap.contDiff (actionCLM Λ⁻¹)))
