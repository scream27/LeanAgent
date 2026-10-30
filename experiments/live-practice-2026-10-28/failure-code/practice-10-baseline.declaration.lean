theorem affine_gaps_lifted_to_interleaved_codes {m : ℕ} {ε : ℕ}
    {e : ℕ} (he : e ≤ (Code.uniqueDecodingRadius (F := A) (ι := ι) (C := MC))) (hε : ε ≥ e + 1)
    (hProximityGapAffineLines :
      e_ε_correlatedAgreementAffineLinesNat (F := F) (C := (MC : Set (ι → A))) (e := e) (ε := ε)) :
    e_ε_correlatedAgreementAffineLinesNat (ι := ι) (F := F) (A := InterleavedSymbol A (Fin m))
      (C := ((MC^⋈(Fin m)) : Set (ι → (InterleavedSymbol A (Fin m))))) (e := e) (ε := ε) := by
  -- 1. Unfold the definition of e_ε_correlatedAgreementAffineLinesNat for the interleaved code C^m.
  -- We must show that for any two words U₀, U₁, if the set of "close" affine
  -- combinations (R*) is large, then U₀ and U₁ have correlated agreement with C^m.
  intro U₀ U₁ hR_prob_shaded_affine_comb_gt_threshold
  -- `⊢ ModuleCode.correlatedAgreement₂ U₀ U₁ ↑e, i.e. |D| ≤ e`

  -- 2. Assume the hypothesis: |R*| > ε
  let hR_star_card_gt_ε := probShadedAffineCombInterleavedCodeword_gt_threshold_iff
    (F := F) (A := A) (ι := ι) (MC := MC) (m := m)
    (U₀ := U₀) (U₁ := U₁) (ε := ε) (e := e).mp hR_prob_shaded_affine_comb_gt_threshold
  have hR_star_card_gt1 : (R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m)
    (e := e) U₀ U₁).card > 1 := by omega  -- |R*| > ε ≥ e + 1 ≥ 1
  have hR_star_card_gt1_Real : ((R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m)
    (e := e) U₀ U₁).card : ℝ) > 1 := by
    exact Nat.cast_gt_Real_one (R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m)
      (e := e) U₀ U₁).card hR_star_card_gt1
  -- 3. Use the hypothesis on the base code C (hProximityGapAffineLines)
  -- and the fact that |R*| > ε to construct the candidate
  -- interleaved codewords V₀ and V₁ in C^m.
  set V := constructInterleavedCodewordsAndRowWiseCA (F := F) (A := A) (ι := ι) (C := MC) (m := m)
    (U₀ := U₀) (U₁ := U₁)
    hProximityGapAffineLines (hR_star_card_gt_ε)
  let V₀ := V.1; let V₁ := V.2.1; let h_row_agreement := V.2.2
  set D := disagreementSet U₀ U₁ V₀ V₁
  have h_D_card_le_n : D.card ≤ Fintype.card ι := by
    dsimp only [disagreementSet, ne_eq, D]
    let res := Finset.card_filter_le (s := Finset.univ (α := ι))
      (p := fun colIdx => ¬U₀ colIdx = V₀.val colIdx ∨ ¬U₁ colIdx = V₁.val colIdx)
    rw [Finset.card_univ] at res
    convert res
  have h_D_le_D_mul_R_star_card: D.card ≤ D.card * (R_star (A := A) (F := F) (ι := ι)
    (C := MC) (m := m) (e := e) U₀ U₁).card := by
    conv_lhs => rw [←Nat.mul_one D.card]
    apply Nat.mul_le_mul_left; exact Nat.one_le_of_lt hR_star_card_gt_ε
  -- `e · |R*| ≥ |D| · (|R*| - 1)
  have h_e_mul_Rstar_card_ge:
    e * (R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card
      ≥ D.card * (R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card
        - D.card := by
    -- This comes from lemma 3.3: |R**| ≤ |R*|(n - |D|) + |D|
    -- and lemma 3.4: |R**| ≥ (n - e)|R*|
    have h_lemma_3_3 := R_star_star_upper_bound (MC := MC) (ε := ε) (m := m) (e := e)
      U₀ U₁ hProximityGapAffineLines hR_star_card_gt_ε
    have h_lemma_3_4 := R_star_star_lower_bound (MC := MC) (ε := ε) (m := m) (e := e)
      (U₀ := U₀) (U₁ := U₁) (he := he) hProximityGapAffineLines hR_star_card_gt_ε
    simp only [ge_iff_le] at h_lemma_3_3 h_lemma_3_4
    set n := Fintype.card ι
    -- So (n - e)|R*| ≤ |R**| ≤ |R*|(n - |D|) + |D|
    have h_le_trans := le_trans h_lemma_3_4 h_lemma_3_3
    -- ↔ n * |R*| - e * |R*| ≤ n * |R*| - |D| * |R*| + |D|
    rw [Nat.sub_mul (n := n) (m := e), Nat.mul_sub (n := (R_star (A := A) (F := F)
      (ι := ι) (C := MC) U₀ U₁).card), Nat.mul_comm (n := (R_star (A := A) (F := F) (ι := ι)
        (C := MC) U₀ U₁).card) (m := D.card)] at h_le_trans
    -- ↔ e * |R*| ≥ |D| * (|R*| - 1) (Q.E.D)
    have h_le_trans: n * #(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁)
      - e * #(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁)
      ≤ n * #(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁)
        - #D * #(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁) + #D := by
      conv_rhs =>
        rw [Nat.mul_comm n (#(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁))]
      exact h_le_trans
    -- conv_rhs at h_le_trans => enter [2]; rw [←Nat.mul_one #D]
    rw [Nat.sub_add_eq_sub_sub_rev (a := n * #(R_star (A := A) (F := F) (ι := ι) (C := MC) U₀ U₁))
      (b :=  #D * #(R_star (A := A) (F := F) (ι := ι) (C := MC) U₀ U₁)) (c := #D)
        (h1 := h_D_le_D_mul_R_star_card)
      (h2 := Nat.mul_le_mul_right (#(R_star (A := A) (F := F) (ι := ι) (C := MC) U₀ U₁))
        h_D_card_le_n)] at h_le_trans
    have h_le: #D * #(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁) - #D
      ≤ n * #(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁) := by
      apply Nat.sub_le_of_le_add; apply le_add_of_le_left;
      exact
        Nat.mul_le_mul_right (#(R_star (A := A) (F := F) (ι := ι) (C := MC) U₀ U₁)) h_D_card_le_n
    rw [Nat.sub_le_sub_iff_left (k := n * #(R_star (A := A) (F := F) (ι := ι) (C := MC) U₀ U₁))
      (h := h_le)] at h_le_trans
    exact h_le_trans
  have h_e_mul_Rstar_card_ge_Real: (e : ℝ) * (R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m)
    (e := e) U₀ U₁).card ≥ D.card * (R_star (A := A) (F := F) (ι := ι) (C := MC)
      (m := m) (e := e) U₀ U₁).card - D.card := by
    rw [←Nat.cast_mul, ←Nat.cast_mul, ←Nat.cast_sub (h := h_D_le_D_mul_R_star_card)]
    rw [ge_iff_le]
    rw [Nat.cast_le]
    exact h_e_mul_Rstar_card_ge
  -- `|D| ≤ e * (|R*| / (|R*| - 1))
  have h_D_card_le_e_mul_R_div_R_succ: D.card ≤ e *
    ((R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card : ℝ) /
    ((R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card - 1) := by
    rw [le_div_iff₀ (hc := by rw [sub_pos]; exact hR_star_card_gt1_Real)]
    rw [mul_sub, mul_one]
    exact h_e_mul_Rstar_card_ge_Real
  -- e * (|R*| / (|R*| - 1)) < e + 1 ↔ e * |R*| < e * |R*| - (e + 1) + |R*|
    -- ↔ 0 < |R*| - (e + 1) ↔ e + 1 < |R*|
  have h_e_mul_R_div_R_succ_lt: e * ((R_star (A := A) (F := F) (ι := ι) (C := MC)
    (m := m) (e := e) U₀ U₁).card : ℝ)
    / ((R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card - 1) < e + 1 := by
    exact e_mul_R_div_R_sub_1_lt_e_add_1_real (e := e) (R := (R_star (A := A)
      (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card) (hR_gt_e_add_1 := by omega)
  have h_D_card_le_e: D.card ≤ e := by
    apply Nat.le_of_lt_succ;
    have res := lt_of_le_of_lt (a := (#D : ℝ))
      (b := e * ((R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card : ℝ)
        / ((R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card - 1))
        (c := (e + 1 : ℝ)) (hab := h_D_card_le_e_mul_R_div_R_succ) (hbc := h_e_mul_R_div_R_succ_lt)
    rw [←Nat.cast_add_one, Nat.cast_lt] at res
    exact res
  dsimp only [D] at h_D_card_le_e
  exact (D_card_le_e_implies_interleaved_correlatedAgreement₂ (MC := MC)
    (m := m) (e := e) (ε := ε) U₀ U₁ hProximityGapAffineLines hR_star_card_gt_ε) (h_D_card_le_e)