lemma time_deriv_time_deriv_electricField_of_isExtrema {A : ElectromagneticPotential d}
    {𝓕 : FreeSpace}
    (hA : ContDiff ℝ ∞ A) (J : LorentzCurrentDensity d)
    (hJ : ContDiff ℝ ∞ J) (h : IsExtrema 𝓕 A J)
    (t : Time) (x : Space d) (i : Fin d) :
    ∂ₜ (∂ₜ (A.electricField 𝓕.c · x i)) t =
      𝓕.c ^ 2 * ∑ j, (∂[j] (∂[j] (A.electricField 𝓕.c t · i)) x) -
      𝓕.c ^ 2 / 𝓕.ε₀ * ∂[i] (J.chargeDensity 𝓕.c t ·) x -
      𝓕.c ^ 2 * 𝓕.μ₀ * ∂ₜ (J.currentDensity 𝓕.c · x i) t := by
  have hEs : ∀ j, ContDiff ℝ 2 (fun y => A.electricField 𝓕.c t y j) :=
    fun j => electricField_apply_contDiff_space (i := j) (hA.of_le (right_eq_inf.mp rfl)) t
  have hEd : ∀ j k, Differentiable ℝ (∂[k] (fun y => A.electricField 𝓕.c t y j)) :=
    fun j k => Space.deriv_differentiable (hEs j) k
  have hBt : ∀ j, Differentiable ℝ
      (fun s => ∂[j] (fun y => A.magneticFieldMatrix 𝓕.c s y (j, i)) x) :=
    fun j => Space.space_deriv_differentiable_time (i := j)
      (magneticFieldMatrix_contDiff _ (hA.of_le (right_eq_inf.mp rfl)) (j, i)) x
  have hJt : Differentiable ℝ (fun s => J.currentDensity 𝓕.c s x i) :=
    LorentzCurrentDensity.currentDensity_apply_differentiable_time (hJ.differentiable (by decide)) x i
  calc _
    _ = 1 / (𝓕.μ₀ * 𝓕.ε₀) * ∑ j, (∂[j] (fun x => ∂[j] (A.electricField 𝓕.c t · i) x) x) -
        1 / (𝓕.μ₀ * 𝓕.ε₀) * ∑ j, (∂[i] (fun x => ∂[j] (A.electricField 𝓕.c t · j) x) x) -
        1 / 𝓕.ε₀ * ∂ₜ (J.currentDensity 𝓕.c · x i) t := by
        conv_lhs =>
          enter [1]
          change fun t => ∂ₜ (A.electricField 𝓕.c · x i) t
          enter [t]
          rw [Time.deriv_euclid (electricField_differentiable_time
            (hA.of_le (right_eq_inf.mp rfl)) _),
            time_deriv_electricField_of_isExtrema hA J hJ h]
        rw [Time.deriv_eq, fderiv_fun_sub ((Differentiable.fun_sum fun j _ => hBt j).const_mul _).differentiableAt
          (hJt.differentiableAt.const_mul _), fderiv_const_mul
          (Differentiable.fun_sum fun j _ => hBt j).differentiableAt, fderiv_const_mul hJt.differentiableAt]
        simp only [FunLike.coe_sub, Pi.sub_apply, _root_.smul_apply, smul_eq_mul, ← Time.deriv_eq]
        rw [Time.deriv_fun_sum _ _ fun i _ => (hBt i).differentiableAt]
        simp only [Space.time_deriv_comm_space_deriv
          (magneticFieldMatrix_contDiff _ (hA.of_le (right_eq_inf.mp rfl)) _),
          time_deriv_magneticFieldMatrix _ (hA.of_le ENat.LEInfty.out), ← mul_sub, ← Finset.sum_sub_distrib]
        congr 3
        funext j
        rw [Space.deriv_eq_fderiv_basis, fderiv_fun_sub (hEd _ _).differentiableAt (hEd _ _).differentiableAt]
        simp only [_root_.sub_apply, ← deriv_eq_fderiv_basis, sub_right_inj]
        rw [Space.deriv_commute _ (hEs _), Space.deriv_eq_fderiv_basis]
      _ = 1 / (𝓕.μ₀ * 𝓕.ε₀) * ∑ j, (∂[j] (∂[j] (A.electricField 𝓕.c t · i)) x) -
          1 / (𝓕.μ₀ * 𝓕.ε₀ ^ 2) * ∂[i] (J.chargeDensity 𝓕.c t ·) x -
          1 / 𝓕.ε₀ * ∂ₜ (J.currentDensity 𝓕.c · x i) t := by
        congr 2
        rw [isExtrema_iff_gauss_ampere_magneticFieldMatrix hA J hJ] at h
        trans 1 / (𝓕.μ₀ * 𝓕.ε₀) * ∂[i] (fun x => ∑ j, ∂[j] (A.electricField 𝓕.c t · j) x) x
        · rw [Space.deriv_eq_fderiv_basis, fderiv_fun_sum fun j _ => (hEd j j).differentiableAt]
          simp only [_root_.sum_apply, ← deriv_eq_fderiv_basis]
        change _ * ∂[i] (fun x => (∇ ⬝ (A.electricField 𝓕.c t)) x) x = _
        simp only [(h t _).1, div_eq_inv_mul, Space.deriv_eq_fderiv_basis, fderiv_const_mul
          ((LorentzCurrentDensity.chargeDensity_differentiable_space (hJ.differentiable (by decide)) t) _)]
        simp only [_root_.smul_apply, smul_eq_mul, ← Space.deriv_eq_fderiv_basis]
        ring
      _ = 𝓕.c ^ 2 * ∑ j, (∂[j] (∂[j] (A.electricField 𝓕.c t · i)) x) -
            𝓕.c ^ 2 / 𝓕.ε₀ * ∂[i] (J.chargeDensity 𝓕.c t ·) x -
            𝓕.c ^ 2 * 𝓕.μ₀ * ∂ₜ (J.currentDensity 𝓕.c · x i) t := by
          simp only [one_div, mul_inv_rev, FreeSpace.c_sq]
          field_simp