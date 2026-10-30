lemma time_deriv_time_deriv_magneticFieldMatrix_of_isExtrema {A : ElectromagneticPotential d}
    {𝓕 : FreeSpace}
    (hA : ContDiff ℝ ∞ A) (J : LorentzCurrentDensity d)
    (hJ : ContDiff ℝ ∞ J) (h : IsExtrema 𝓕 A J)
    (t : Time) (x : Space d) (i j : Fin d) :
    ∂ₜ (∂ₜ (A.magneticFieldMatrix 𝓕.c · x (i, j))) t =
    𝓕.c ^ 2 * ∑ k, ∂[k] (∂[k] (A.magneticFieldMatrix 𝓕.c t · (i, j))) x +
    𝓕.ε₀⁻¹ * (∂[j] (J.currentDensity 𝓕.c t · i) x - ∂[i] (J.currentDensity 𝓕.c t · j) x) := by
  have hcd : ∀ ij, ContDiff ℝ 2 (fun y => A.magneticFieldMatrix 𝓕.c t y ij) :=
    fun ij => magneticFieldMatrix_space_contDiff _ (hA.of_le (right_eq_inf.mp rfl)) t ij
  have hsd : ∀ ij k, Differentiable ℝ (∂[k] (fun y => A.magneticFieldMatrix 𝓕.c t y ij)) :=
    fun ij k => Space.deriv_differentiable (hcd ij) k
  have hJd : ∀ i, Differentiable ℝ (fun x => J.currentDensity 𝓕.c t x i) :=
    fun i => LorentzCurrentDensity.currentDensity_apply_differentiable_space
      (hJ.differentiable (by simp)) t i
  rw [time_deriv_time_deriv_magneticFieldMatrix A (hA.of_le (ENat.LEInfty.out))]
  conv_lhs =>
    enter [2, 2, x]
    rw [time_deriv_electricField_of_isExtrema hA J hJ h]
  conv_lhs =>
    enter [1, 2, x]
    rw [time_deriv_electricField_of_isExtrema hA J hJ h]
  rw [Space.deriv_eq_fderiv_basis]
  rw [fderiv_fun_sub ((Differentiable.fun_sum fun i _ => hsd _ i).const_mul _).differentiableAt
      ((hJd _).const_mul _).differentiableAt,
    fderiv_const_mul (Differentiable.fun_sum fun i _ => hsd _ i).differentiableAt,
    fderiv_const_mul (hJd _).differentiableAt,
    fderiv_fun_sum fun i _ => (hsd _ i).differentiableAt]
  conv_lhs =>
    enter [2]
    rw [Space.deriv_eq_fderiv_basis]
    rw [fderiv_fun_sub ((Differentiable.fun_sum fun i _ => hsd _ i).const_mul _).differentiableAt
        ((hJd _).const_mul _).differentiableAt,
    fderiv_const_mul (Differentiable.fun_sum fun i _ => hsd _ i).differentiableAt,
    fderiv_const_mul (hJd _).differentiableAt,
    fderiv_fun_sum fun i _ => (hsd _ i).differentiableAt]
  simp [← Space.deriv_eq_fderiv_basis, FreeSpace.c_sq]
  field_simp
  conv_rhs =>
    enter [1, 2, k, 2, x]
    rw [magneticFieldMatrix_space_deriv_eq A (hA.of_le (right_eq_inf.mp rfl))]
  conv_rhs =>
    enter [1, 2, k]
    rw [Space.deriv_eq_fderiv_basis]
    rw [fderiv_fun_sub (hsd _ _).differentiableAt (hsd _ _).differentiableAt]
    simp [← Space.deriv_eq_fderiv_basis]
    rw [Space.deriv_commute _ (hcd _)]
    enter [2]
    rw [Space.deriv_commute _ (hcd _)]
  simp only [Finset.sum_sub_distrib]
  ring