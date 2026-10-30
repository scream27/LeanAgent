/-- **Lemma 3.4 (DG25): Lower Bound on R** Cardinality**
Context:
- Same as Lemma 3.2, including hypotheses on `C`, `e`, `V₀`, `V₁`, `R_star`.
- `R_star_star` is the set of pairs `(r, j)` where `r ∈ R_star` and column `j` of `Uᵣ`
equals column `j` of `Vᵣ`.
Statement: The number of agreeing column pairs `(r, j)` is at least the number
of parameters in `R_star` times the number of columns guaranteed to agree (`n - e`)
for each `r` (using Lemma 3.2), i.e. `|R**| ≥ (n - e) * |R*|`
-/
lemma R_star_star_lower_bound
    (U₀ U₁ : InterleavedWord A (Fin m) ι)
    (he : e ≤ (Code.uniqueDecodingRadius (F := A) (ι := ι) (C := MC)))
    (hC_gap : e_ε_correlatedAgreementAffineLinesNat (A := A) (ι := ι) (C := MC) e ε)
    (hR_star_card : (R_star (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card > ε) :
      let ⟨V₀, V₁, _⟩ := constructInterleavedCodewordsAndRowWiseCA (F := F)
        (A := A) (ι := ι) (C := MC) (U₀ := U₀) (U₁ := U₁) (hC_gap := by exact hC_gap)
        (hR_star_card := hR_star_card)
      (R_star_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁ V₀ V₁).card
        >= (Fintype.card ι - e) *
          (R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁).card := by
  classical
  /- DG25 Proof Sketch:
     Sum over r ∈ R*. For each such r:
     Apply Lemma 3.2 (using h_agree, he_udr, hR_star): Δ^m(Uᵣ, Vᵣ) ≤ e.
     By definition of Δ^m, this means Uᵣ and Vᵣ agree on ≥ n - e columns j.
     So, row r contributes ≥ n - e to |R**|.
     Summing gives |R**| ≥ |R*| * (n - e).
  -/
  -- 1. Define local variables
  let V₀ := (constructInterleavedCodewordsAndRowWiseCA (F := F)
        (A := A) (ι := ι) (C := MC) (U₀ := U₀) (U₁ := U₁) (hC_gap := by exact hC_gap)
        (hR_star_card := hR_star_card)).1
  let V₁ := (constructInterleavedCodewordsAndRowWiseCA (F := F)
        (A := A) (ι := ι) (C := MC) (U₀ := U₀) (U₁ := U₁) (hC_gap := by exact hC_gap)
        (hR_star_card := hR_star_card)).2.1
  let n := Fintype.card ι
  let R_s := R_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁
  let R_ss := R_star_star (A := A) (F := F) (ι := ι) (C := MC) (m := m) (e := e) U₀ U₁ V₀.val V₁.val
  simp only [ge_iff_le]
  simp only [R_star_star]
  rw [Finset.card_filter]
  rw [Finset.sum_product]
  have h_card_ge_per_r: ∀ r : R_star (A := A) (F := F) (ι := ι) (C := MC)
    (e := e) U₀ U₁, (Fintype.card ι - e) ≤ (∑ j, if
      affineLineEvaluation (F := F) U₀ U₁ (r, j).1 (r, j).2
      = affineLineEvaluation (F := F) V₀.val V₁.val (r, j).1 (r, j).2 then 1 else 0) := by
    intro r
      -- Let Uᵣ and Vᵣ be the affine points for this r
    let Uᵣ := affineLineEvaluation (F := F) U₀ U₁ r
    let Vᵣ := affineLineEvaluation (F := F) V₀.val V₁.val r
    -- The sum is the number of agreeing columns, which is `n - hammingDist(Uᵣ, Vᵣ)`
    have h_sum_eq_agreeing_cols :
        (∑ j, if Uᵣ j = Vᵣ j then 1 else 0) = n - Δ₀(Uᵣ, Vᵣ) := by
      -- 1. `∑ j, if P j then 1 else 0` is the definition of `(Finset.filter P Finset.univ).card`
      rw [Finset.sum_boole]
      -- 2. Unfold the notation
      -- `n` is `(Finset.univ : Finset ι).card`
      dsimp only [Nat.cast_id, n]
      rw [←Finset.card_univ]
      -- `Δ₀(Uᵣ, Vᵣ)` is `hammingDist Uᵣ Vᵣ`
      unfold hammingDist
      apply Nat.eq_sub_of_add_eq
      rw [Finset.card_filter, Finset.card_filter]
      rw [← Finset.sum_add_distrib]
      simp_rw [ne_eq]
      -- simp will solve the `ite` logic and apply `sum_const_one`
      simp only [ite_not, card_univ]
      have h_inner :
          ∀ x, ((if Uᵣ x = Vᵣ x then 1 else 0) + if Uᵣ x = Vᵣ x then 0 else 1) = 1 := fun x => by
        by_cases h : Uᵣ x = Vᵣ x
        · simp only [h, if_true]
        · simp only [h, if_false]
      simp_rw [h_inner]
      simp only [sum_const, card_univ, smul_eq_mul, mul_one]
    rw [h_sum_eq_agreeing_cols]
    -- Goal: n - e ≤ n - hammingDist Uᵣ Vᵣ
    -- This is equivalent to `hammingDist Uᵣ Vᵣ ≤ e`
    -- We use `Nat.sub_le_sub_left_iff` which requires `hammingDist Uᵣ Vᵣ ≤ n`
    have h_dist_le_n : hammingDist Uᵣ Vᵣ ≤ e := by
    -- This is exactly the conclusion of Lemma 3.2 (affineWord_close_to_affineInterleavedCodeword)
      let res := affineWord_close_to_affineInterleavedCodeword (U₀ := U₀) (U₁ := U₁)
        (he := he) (hC_gap := by exact hC_gap) (hR_star_card := hR_star_card) (r := r)
      simp only [Fin.isValue, eq_mpr_eq_cast, cast_eq, ENNReal.coe_natCast,
        Lean.Elab.WF.paramLet] at res
      exact res
    exact Nat.sub_le_sub_left h_dist_le_n (Fintype.card ι)
  have h_left : (Fintype.card ι - e) * #(R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁)
    = ∑ r ∈ R_star (A := A) (F := F) (ι := ι) (C := MC) (e := e) U₀ U₁, (Fintype.card ι - e) := by
    rw [Finset.sum_const]
    simp only [smul_eq_mul]
    exact Nat.mul_comm (Fintype.card ι - e) #(R_star (A := A) (F := F) (ι := ι) (C := MC) U₀ U₁)
  rw [h_left]
  apply Finset.sum_le_sum
  intro r hr_mem
  exact h_card_ge_per_r (Subtype.mk r hr_mem)