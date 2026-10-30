/-- Remark 1.2.10 -/
theorem Box.sum_volume_eq {d:ℕ} (B B': ℕ → Box d) (hdisj: Pairwise (Function.onFun AlmostDisjoint B)) (hdisj': Pairwise (Function.onFun AlmostDisjoint B')) (hcover: (⋃ n, (B n).toSet) = (⋃ n, (B' n).toSet)) :
    ∑' n, (B n).volume = ∑' n, (B' n).volume := by
  -- Establish outer measure equality using union_of_almost_disjoint (Lemma 1.2.9)
  have hB := Lebesgue_outer_measure.union_of_almost_disjoint hdisj
  have hB' := Lebesgue_outer_measure.union_of_almost_disjoint hdisj'
  -- Simplify: m*(Bᵢ) = |Bᵢ|.toEReal for each box
  have h_box : ∀ i, Lebesgue_outer_measure (B i).toSet = (B i).volume.toEReal := by
    intro i
    rw [Lebesgue_outer_measure.elementary _ (IsElementary.box _), IsElementary.measure_of_box]
  have h_box' : ∀ i, Lebesgue_outer_measure (B' i).toSet = (B' i).volume.toEReal := by
    intro i
    rw [Lebesgue_outer_measure.elementary _ (IsElementary.box _), IsElementary.measure_of_box]
  simp_rw [h_box] at hB
  simp_rw [h_box'] at hB'
  -- Now: ∑' |B n|.toEReal = m*(⋃ B n) = m*(⋃ B' n) = ∑' |B' n|.toEReal
  have h_eq : (∑' n, ((B n).volume : EReal)) = (∑' n, ((B' n).volume : EReal)) := by
    rw [← hB, hcover, hB']
  -- Define ENNReal versions and work through ENNReal
  have h_vol_nn : ∀ n, 0 ≤ (B n).volume := fun n => Box.volume_nonneg _
  have h_vol_nn' : ∀ n, 0 ≤ (B' n).volume := fun n => Box.volume_nonneg _
  let f : ℕ → ENNReal := fun n => ENNReal.ofReal (B n).volume
  let f' : ℕ → ENNReal := fun n => ENNReal.ofReal (B' n).volume
  -- Key: (B n).volume.toEReal = (f n : EReal) for nonneg volumes
  have hf_eq : ∀ n, ((B n).volume : EReal) = (f n : EReal) := fun n => by
    simp only [f, EReal.coe_ennreal_ofReal, max_eq_left (h_vol_nn n)]
  have hf'_eq : ∀ n, ((B' n).volume : EReal) = (f' n : EReal) := fun n => by
    simp only [f', EReal.coe_ennreal_ofReal, max_eq_left (h_vol_nn' n)]
  -- Rewrite h_eq using ENNReal
  simp_rw [hf_eq, hf'_eq] at h_eq
  -- ENNReal tsums commute with coercion to EReal
  have h_ennreal_eq : (∑' n, f n : ENNReal) = ∑' n, f' n := by
    have h_coe : ∀ (g : ℕ → ENNReal), (∑' n, g n : ENNReal).toEReal = ∑' n, (g n : EReal) := by
      intro g
      let φ : ENNReal →+ EReal := {
        toFun := (↑·)
        map_zero' := by simp
        map_add' := EReal.coe_ennreal_add
      }
      exact Summable.map_tsum ENNReal.summable φ continuous_coe_ennreal_ereal
    rw [← h_coe f, ← h_coe f'] at h_eq
    exact EReal.coe_ennreal_eq_coe_ennreal_iff.mp h_eq
  -- Transfer back to ℝ using ENNReal.toReal
  have h_toReal_eq : (∑' n, f n).toReal = (∑' n, f' n).toReal := by rw [h_ennreal_eq]
  -- Use ENNReal.tsum_toReal_eq for finite-valued functions
  have hf_ne_top : ∀ n, f n ≠ ⊤ := fun n => ENNReal.ofReal_ne_top
  have hf'_ne_top : ∀ n, f' n ≠ ⊤ := fun n => ENNReal.ofReal_ne_top
  rw [ENNReal.tsum_toReal_eq hf_ne_top, ENNReal.tsum_toReal_eq hf'_ne_top] at h_toReal_eq
  -- Simplify: (ENNReal.ofReal x).toReal = x for x ≥ 0
  simp only [f, f', ENNReal.toReal_ofReal (h_vol_nn _), ENNReal.toReal_ofReal (h_vol_nn' _)] at h_toReal_eq
  exact h_toReal_eq