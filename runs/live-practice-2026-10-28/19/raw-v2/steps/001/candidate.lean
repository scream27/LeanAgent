lemma triangle_or_blueStar_from_block2
    (color : Sym2 V → Fin 2)
    (h6 : 6 ≤ (redBlock2 color).card)
    (i : Fin 3)
    (hAdj : G.Adj apex (A2 i))
    (hRedApexA2 : color (Sym2.mk (apex, A2 i)) = 1) :
    hasMonoTriangle G color 1 ∨ hasMonoStar G color 0 5 := by
  classical
  have hy0_in : A2 i ∈ redBlock2 color := A2_mem_redBlock2_of_red color i hAdj hRedApexA2
  have h5 :
    5 ≤ ((redBlock2 color).erase (A2 i)).card := by
    have hcard :
        ((redBlock2 color).erase (A2 i)).card + 1 = (redBlock2 color).card :=
      Finset.card_erase_add_one hy0_in
    have : 6 ≤ ((redBlock2 color).erase (A2 i)).card + 1 := by simpa [hcard] using h6
    exact (Nat.succ_le_succ_iff.mp this)
  obtain ⟨T, hTsub, hTcard⟩ :=
    Finset.exists_subset_card_eq ((redBlock2 color).erase (A2 i)) h5

  have hAdjAll : ∀ {y}, y ∈ T → G.Adj (A2 i) y := by
    intro y hy
    have hy_erase : y ∈ (redBlock2 color).erase (A2 i) := hTsub hy
    have hy_ne : y ≠ A2 i := (Finset.mem_erase.mp hy_erase).1
    have hy_in : y ∈ redBlock2 color := (Finset.mem_erase.mp hy_erase).2
    rcases Finset.mem_filter.1 hy_in with ⟨_, hy_block2⟩
    cases y with
    | A2 j =>
        have hij : j ≠ i := by intro h; exact hy_ne (by simp [h])
        have : i ≠ j := by simpa [ne_comm] using hij
        simp [adj_A2A2, this]
    | B2 _  => simp [adj_A2B2]
    | A1 _  => simp [isA1] at hy_block2
    | B1 _  => simp [isB1] at hy_block2
    | apex  => simp [G, GAdj]

  by_cases hTri : ∃ y ∈ T, color (Sym2.mk (A2 i, y)) = 1
  · rcases hTri with ⟨y, hyT, hyRedA2y⟩
    have hy_erase : y ∈ (redBlock2 color).erase (A2 i) := hTsub hyT
    have hy_ne : y ≠ A2 i := (Finset.mem_erase.mp hy_erase).1
    have hy_in : y ∈ redBlock2 color := (Finset.mem_erase.mp hy_erase).2
    rcases Finset.mem_filter.1 hy_in with ⟨hy_RN, hy_block2⟩
    rcases Finset.mem_filter.1 hy_RN with ⟨hyAdjApex, hyRedApexY⟩
    have hyAdjA2Y := hAdjAll hyT
    refine Or.inl ?triangle
    refine ⟨apex, A2 i, y, ?_, ?_, ?_, ?_, ?_, ?_⟩
    · simp [hAdj]
    · exact hyAdjA2Y
    · aesop
    · simpa using hRedApexA2
    · exact hyRedA2y
    · simpa using hyRedApexY
  ·
    have hAllBlue : ∀ {y}, y ∈ T → color (Sym2.mk (A2 i, y)) = 0 := by
      intro y hy
      have h1 : color (Sym2.mk (A2 i, y)) ≠ 1 := by
        intro contra; exact hTri ⟨y, hy, contra⟩
      have : color (Sym2.mk (A2 i, y)) = 0 ∨ color (Sym2.mk (A2 i, y)) = 1 := by grind
      exact this.resolve_right h1
    have hnotin : A2 i ∉ T := by
      intro hx
      have : A2 i ∈ (redBlock2 color).erase (A2 i) := hTsub hx
      simp at this
    refine Or.inr ?star
    refine ⟨A2 i, T, by simp [hTcard], hnotin, ?_⟩
    intro y hy
    exact ⟨hAdjAll hy, hAllBlue hy⟩
