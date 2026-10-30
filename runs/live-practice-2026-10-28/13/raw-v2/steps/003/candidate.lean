/-- Two dyadic cubes are either almost disjoint or one contains the other. -/
lemma nesting {d:ℕ} {n m : ℤ} {a : Fin d → ℤ} {b : Fin d → ℤ} :
    AlmostDisjoint (DyadicCube n a) (DyadicCube m b) ∨
    (DyadicCube n a).toSet ⊆ (DyadicCube m b).toSet ∨
    (DyadicCube m b).toSet ⊆ (DyadicCube n a).toSet := by
  -- Case analysis on the relationship between n and m
  rcases lt_trichotomy n m with hn | rfl | hm
  · -- n < m: The cube at scale m has smaller cells (2^(-m) < 2^(-n))
    -- Either DyadicCube m b ⊆ DyadicCube n a (if b is in the right position) or almost disjoint
    -- Check if DyadicCube m b ⊆ DyadicCube n a by checking containment of intervals
    by_cases h_subset : ∀ i, (a i : ℝ) / 2^n ≤ (b i : ℝ) / 2^m ∧ ((b i : ℝ) + 1) / 2^m ≤ ((a i : ℝ) + 1) / 2^n
    · -- DyadicCube m b ⊆ DyadicCube n a
      right; right
      intro x hx i hi
      simp only [DyadicCube, BoundedInterval.toSet, Set.mem_Icc] at hx ⊢
      have hxi := hx i hi
      exact ⟨le_trans (h_subset i).1 hxi.1, le_trans hxi.2 (h_subset i).2⟩
    · -- Not contained, so they are almost disjoint
      left
      push_neg at h_subset
      obtain ⟨i, hi⟩ := h_subset
      simp only [AlmostDisjoint, DyadicCube.interior]
      ext x
      simp only [Set.mem_inter_iff, Set.mem_empty_iff_false, iff_false, not_and]
      intro ha hb
      have hai := ha i (Set.mem_univ i)
      have hbi := hb i (Set.mem_univ i)
      have h2n_pos : (0:ℝ) < 2^n := zpow_pos (by norm_num : (0:ℝ) < 2) n
      have h2m_pos : (0:ℝ) < 2^m := zpow_pos (by norm_num : (0:ℝ) < 2) m
      have h_mn_pos : 0 < m - n := Int.sub_pos_of_lt hn
      -- hi says: if a_i/2^n ≤ b_i/2^m then (a_i+1)/2^n < (b_i+1)/2^m
      -- Case 1: a_i/2^n > b_i/2^m (the hypothesis of hi fails)
      -- Case 2: a_i/2^n ≤ b_i/2^m but (a_i+1)/2^n < (b_i+1)/2^m (hi applies)
      by_cases h_left : (b i : ℝ) / 2^m < (a i : ℝ) / 2^n
      · -- b_i/2^m < a_i/2^n: left endpoint of b is before left endpoint of a
        by_cases h_disj : ((b i : ℝ) + 1) / 2^m ≤ (a i : ℝ) / 2^n
        · -- Intervals (b_i/2^m, (b_i+1)/2^m) and (a_i/2^n, (a_i+1)/2^n) don't overlap
          linarith [hai.1, hbi.2]
        · -- Intervals overlap: b_i/2^m < a_i/2^n < (b_i+1)/2^m
          push_neg at h_disj
          -- a_i * 2^(m-n) lies strictly between b_i and b_i+1
          -- But a_i * 2^(m-n) is an integer (since m > n implies m-n > 0)
          have hlo : (b i : ℝ) < (a i : ℝ) * 2^(m-n) := by
            have h1 : (b i : ℝ) / 2^m * 2^m < (a i : ℝ) / 2^n * 2^m := mul_lt_mul_of_pos_right h_left h2m_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2m_pos)] at h1
            calc (b i : ℝ) < (a i : ℝ) / 2^n * 2^m := h1
              _ = (a i : ℝ) * (2^m / 2^n) := by ring
              _ = (a i : ℝ) * 2^(m-n) := by rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
          have hhi : (a i : ℝ) * 2^(m-n) < (b i : ℝ) + 1 := by
            have h1 : (a i : ℝ) / 2^n * 2^m < ((b i : ℝ) + 1) / 2^m * 2^m := mul_lt_mul_of_pos_right h_disj h2m_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2m_pos)] at h1
            calc (a i : ℝ) * 2^(m-n) = (a i : ℝ) * (2^m / 2^n) := by
                    rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
              _ = (a i : ℝ) / 2^n * 2^m := by ring
              _ < (b i : ℝ) + 1 := h1
          -- a_i * 2^(m-n) is an integer in (b_i, b_i+1), contradiction
          have h_int : ∃ k : ℤ, (a i : ℝ) * 2^(m-n) = k := by
            have h_pos_exp : ∃ p : ℕ, m - n = p := ⟨(m-n).toNat, (Int.toNat_of_nonneg (le_of_lt h_mn_pos)).symm⟩
            obtain ⟨p, hp⟩ := h_pos_exp
            use a i * 2^p
            simp only [Int.cast_mul, Int.cast_pow, Int.cast_ofNat]
            congr 1
            rw [hp, zpow_natCast]
          obtain ⟨k, hk⟩ := h_int
          rw [hk] at hlo hhi
          have : (b i : ℤ) < k ∧ k < b i + 1 := ⟨by exact_mod_cast hlo, by exact_mod_cast hhi⟩
          omega
      · -- ¬(b_i/2^m < a_i/2^n), so a_i/2^n ≤ b_i/2^m
        push_neg at h_left
        -- By hi: (a_i+1)/2^n < (b_i+1)/2^m
        have h_right := hi h_left
        by_cases h_disj : ((a i : ℝ) + 1) / 2^n ≤ (b i : ℝ) / 2^m
        · -- Intervals don't overlap
          linarith [hai.2, hbi.1]
        · -- Intervals overlap: b_i/2^m < (a_i+1)/2^n < (b_i+1)/2^m
          push_neg at h_disj
          -- (a_i+1) * 2^(m-n) lies strictly between b_i and b_i+1
          have hlo : (b i : ℝ) < ((a i : ℝ) + 1) * 2^(m-n) := by
            have h1 : (b i : ℝ) / 2^m * 2^m < ((a i : ℝ) + 1) / 2^n * 2^m := mul_lt_mul_of_pos_right h_disj h2m_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2m_pos)] at h1
            calc (b i : ℝ) < ((a i : ℝ) + 1) / 2^n * 2^m := h1
              _ = ((a i : ℝ) + 1) * (2^m / 2^n) := by ring
              _ = ((a i : ℝ) + 1) * 2^(m-n) := by rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
          have hhi : ((a i : ℝ) + 1) * 2^(m-n) < (b i : ℝ) + 1 := by
            have h1 : ((a i : ℝ) + 1) / 2^n * 2^m < ((b i : ℝ) + 1) / 2^m * 2^m := mul_lt_mul_of_pos_right h_right h2m_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2m_pos)] at h1
            calc ((a i : ℝ) + 1) * 2^(m-n) = ((a i : ℝ) + 1) * (2^m / 2^n) := by
                    rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
              _ = ((a i : ℝ) + 1) / 2^n * 2^m := by ring
              _ < (b i : ℝ) + 1 := h1
          -- (a_i+1) * 2^(m-n) is an integer in (b_i, b_i+1), contradiction
          have h_int : ∃ k : ℤ, ((a i : ℝ) + 1) * 2^(m-n) = k := by
            have h_pos_exp : ∃ p : ℕ, m - n = p := ⟨(m-n).toNat, (Int.toNat_of_nonneg (le_of_lt h_mn_pos)).symm⟩
            obtain ⟨p, hp⟩ := h_pos_exp
            use (a i + 1) * 2^p
            simp only [Int.cast_mul, Int.cast_pow, Int.cast_ofNat, Int.cast_add, Int.cast_one]
            congr 1
            rw [hp, zpow_natCast]
          obtain ⟨k, hk⟩ := h_int
          rw [hk] at hlo hhi
          have : (b i : ℤ) < k ∧ k < b i + 1 := ⟨by exact_mod_cast hlo, by exact_mod_cast hhi⟩
          omega
  · -- n = m: Same scale, use almost_disjoint_same_scale or equality
    by_cases hab : a = b
    · subst hab
      right; left
      exact Set.Subset.refl _
    · left
      exact DyadicCube.almost_disjoint_same_scale hab
  · -- m < n: The cube at scale n has smaller cells (2^(-n) < 2^(-m))
    -- Either DyadicCube n a ⊆ DyadicCube m b (if a is in the right position) or almost disjoint
    by_cases h_subset : ∀ i, (b i : ℝ) / 2^m ≤ (a i : ℝ) / 2^n ∧ ((a i : ℝ) + 1) / 2^n ≤ ((b i : ℝ) + 1) / 2^m
    · -- DyadicCube n a ⊆ DyadicCube m b
      right; left
      intro x hx i hi
      simp only [DyadicCube, BoundedInterval.toSet, Set.mem_Icc] at hx ⊢
      have hxi := hx i hi
      exact ⟨le_trans (h_subset i).1 hxi.1, le_trans hxi.2 (h_subset i).2⟩
    · -- Not contained, so they are almost disjoint
      left
      push_neg at h_subset
      obtain ⟨i, hi⟩ := h_subset
      simp only [AlmostDisjoint, DyadicCube.interior]
      ext x
      simp only [Set.mem_inter_iff, Set.mem_empty_iff_false, iff_false, not_and]
      intro ha hb
      have hai := ha i (Set.mem_univ i)
      have hbi := hb i (Set.mem_univ i)
      have h2n_pos : (0:ℝ) < 2^n := zpow_pos (by norm_num : (0:ℝ) < 2) n
      have h2m_pos : (0:ℝ) < 2^m := zpow_pos (by norm_num : (0:ℝ) < 2) m
      have h_nm_pos : 0 < n - m := Int.sub_pos_of_lt hm
      -- hi says: if b_i/2^m ≤ a_i/2^n then (a_i+1)/2^n > (b_i+1)/2^m
      by_cases h_left : (a i : ℝ) / 2^n < (b i : ℝ) / 2^m
      · -- a_i/2^n < b_i/2^m: left endpoint of a is before left endpoint of b
        by_cases h_disj : ((a i : ℝ) + 1) / 2^n ≤ (b i : ℝ) / 2^m
        · -- Intervals don't overlap
          linarith [hai.2, hbi.1]
        · -- Intervals overlap: a_i/2^n < b_i/2^m < (a_i+1)/2^n
          push_neg at h_disj
          -- b_i * 2^(n-m) lies strictly between a_i and a_i+1
          have hlo : (a i : ℝ) < (b i : ℝ) * 2^(n-m) := by
            have h1 : (a i : ℝ) / 2^n * 2^n < (b i : ℝ) / 2^m * 2^n := mul_lt_mul_of_pos_right h_left h2n_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2n_pos)] at h1
            calc (a i : ℝ) < (b i : ℝ) / 2^m * 2^n := h1
              _ = (b i : ℝ) * (2^n / 2^m) := by ring
              _ = (b i : ℝ) * 2^(n-m) := by rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
          have hhi : (b i : ℝ) * 2^(n-m) < (a i : ℝ) + 1 := by
            have h1 : (b i : ℝ) / 2^m * 2^n < ((a i : ℝ) + 1) / 2^n * 2^n := mul_lt_mul_of_pos_right h_disj h2n_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2n_pos)] at h1
            calc (b i : ℝ) * 2^(n-m) = (b i : ℝ) * (2^n / 2^m) := by
                    rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
              _ = (b i : ℝ) / 2^m * 2^n := by ring
              _ < (a i : ℝ) + 1 := h1
          -- b_i * 2^(n-m) is an integer in (a_i, a_i+1), contradiction
          have h_int : ∃ k : ℤ, (b i : ℝ) * 2^(n-m) = k := by
            have h_pos_exp : ∃ p : ℕ, n - m = p := ⟨(n-m).toNat, (Int.toNat_of_nonneg (le_of_lt h_nm_pos)).symm⟩
            obtain ⟨p, hp⟩ := h_pos_exp
            use b i * 2^p
            simp only [Int.cast_mul, Int.cast_pow, Int.cast_ofNat]
            congr 1
            rw [hp, zpow_natCast]
          obtain ⟨k, hk⟩ := h_int
          rw [hk] at hlo hhi
          have : (a i : ℤ) < k ∧ k < a i + 1 := ⟨by exact_mod_cast hlo, by exact_mod_cast hhi⟩
          omega
      · -- ¬(a_i/2^n < b_i/2^m), so b_i/2^m ≤ a_i/2^n
        push_neg at h_left
        -- By hi: (a_i+1)/2^n > (b_i+1)/2^m
        have h_right := hi h_left
        by_cases h_disj : ((b i : ℝ) + 1) / 2^m ≤ (a i : ℝ) / 2^n
        · -- Intervals don't overlap
          linarith [hai.1, hbi.2]
        · -- Intervals overlap: a_i/2^n < (b_i+1)/2^m < (a_i+1)/2^n
          push_neg at h_disj
          -- (b_i+1) * 2^(n-m) lies strictly between a_i and a_i+1
          have hlo : (a i : ℝ) < ((b i : ℝ) + 1) * 2^(n-m) := by
            have h1 : (a i : ℝ) / 2^n * 2^n < ((b i : ℝ) + 1) / 2^m * 2^n := mul_lt_mul_of_pos_right h_disj h2n_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2n_pos)] at h1
            calc (a i : ℝ) < ((b i : ℝ) + 1) / 2^m * 2^n := h1
              _ = ((b i : ℝ) + 1) * (2^n / 2^m) := by ring
              _ = ((b i : ℝ) + 1) * 2^(n-m) := by rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
          have hhi : ((b i : ℝ) + 1) * 2^(n-m) < (a i : ℝ) + 1 := by
            have h1 : ((b i : ℝ) + 1) / 2^m * 2^n < ((a i : ℝ) + 1) / 2^n * 2^n := mul_lt_mul_of_pos_right h_right h2n_pos
            simp only [div_mul_cancel₀ _ (ne_of_gt h2n_pos)] at h1
            calc ((b i : ℝ) + 1) * 2^(n-m) = ((b i : ℝ) + 1) * (2^n / 2^m) := by
                    rw [← zpow_sub₀ (by norm_num : (2:ℝ) ≠ 0)]
              _ = ((b i : ℝ) + 1) / 2^m * 2^n := by ring
              _ < (a i : ℝ) + 1 := h1
          -- (b_i+1) * 2^(n-m) is an integer in (a_i, a_i+1), contradiction
          have h_int : ∃ k : ℤ, ((b i : ℝ) + 1) * 2^(n-m) = k := by
            have h_pos_exp : ∃ p : ℕ, n - m = p := ⟨(n-m).toNat, (Int.toNat_of_nonneg (le_of_lt h_nm_pos)).symm⟩
            obtain ⟨p, hp⟩ := h_pos_exp
            use (b i + 1) * 2^p
            simp only [Int.cast_mul, Int.cast_pow, Int.cast_ofNat, Int.cast_add, Int.cast_one]
            congr 1
            rw [hp, zpow_natCast]
          obtain ⟨k, hk⟩ := h_int
          rw [hk] at hlo hhi
          have : (a i : ℤ) < k ∧ k < a i + 1 := ⟨by exact_mod_cast hlo, by exact_mod_cast hhi⟩
          omega
