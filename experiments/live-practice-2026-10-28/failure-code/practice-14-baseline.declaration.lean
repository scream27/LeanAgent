/-- Elementary measure is translation-invariant: μ(E + {x}) = μ(E). -/
lemma IsElementary.measure_of_translate {d:ℕ} {E: Set (EuclideanSpace' d)}
(hE: IsElementary E) (x: EuclideanSpace' d):
  (hE.translate x).measure = hE.measure := by
  -- Strategy:
  -- 0. Case split: E = ∅ or E ≠ ∅
  --    a. Empty case: E = ∅ → E + {x} = ∅, both measures are 0
  --    b. Nonempty case: E ≠ ∅, proceed with partition translation
  -- 1. Get partition T of E: E = ⋃ B ∈ T, B.toSet (from hE.partition)
  -- 2. For each B ∈ T, use Box.volume_of_translate to get B' with B'.toSet = B.toSet + {x} and |B'|ᵥ = |B|ᵥ
  -- 3. Construct T' = {B' | B ∈ T} (using choose to get the translated boxes)
  -- 4. Show T' is pairwise disjoint (translation preserves disjointness)
  -- 5. Show E + {x} = ⋃ B' ∈ T', B'.toSet (translation distributes over union)
  -- 6. Apply measure_eq: (hE.translate x).measure = ∑ B' ∈ T', |B'|ᵥ = ∑ B ∈ T, |B|ᵥ = hE.measure
  classical
  by_cases h_empty : E = ∅
  · -- Empty case: E = ∅ → E + {x} = ∅, both measures are 0
    subst h_empty
    simp [IsElementary.measure_of_empty]
  · -- Nonempty case: E ≠ ∅
    -- Step 1: Get partition T of E, then filter to nonempty boxes
    set T := hE.partition.choose
    have hT_disj : T.toSet.PairwiseDisjoint Box.toSet := hE.partition.choose_spec.1
    have hE_eq : E = ⋃ B ∈ T, B.toSet := hE.partition.choose_spec.2
    -- Filter to nonempty boxes only (empty boxes contribute 0 to measure anyway)
    set T := T.filter (fun B => B.toSet.Nonempty) with hT_def
    have hT_disj : T.toSet.PairwiseDisjoint Box.toSet := by
      intro B₁ hB₁ B₂ hB₂ hB₁B₂
      simp only [Finset.mem_coe] at hB₁ hB₂
      exact hE.partition.choose_spec.1 (Finset.mem_of_mem_filter B₁ hB₁) (Finset.mem_of_mem_filter B₂ hB₂) hB₁B₂
    have hE_eq : E = ⋃ B ∈ T, B.toSet := by
      rw [hE_eq]
      ext y; simp
      constructor
      · intro ⟨B, hB, hy⟩
        exact ⟨B, Finset.mem_filter.mpr ⟨hB, ⟨y, hy⟩⟩, hy⟩
      · intro ⟨B, hB, hy⟩
        exact ⟨B, Finset.mem_of_mem_filter B hB, hy⟩
    have hT_nonempty : ∀ B ∈ T, B.toSet.Nonempty := by
      intro B hB
      exact (Finset.mem_filter.mp hB).2
    -- Step 2-3: Construct translated partition T'
    choose f hf using fun B : Box d => Box.volume_of_translate B x
    set T' := T.image f
    have hf_spec : ∀ B ∈ T, (f B).toSet = B.toSet + {x} ∧ |f B|ᵥ = |B|ᵥ := fun B hB => hf B
    -- Helper: f is injective on T (all boxes in T are nonempty by construction)
    have hf_inj : ∀ B₁ B₂, B₁ ∈ T → B₂ ∈ T → f B₁ = f B₂ → B₁ = B₂ := by
      intro B₁ B₂ hB₁ hB₂ h_eq
      have h_set_eq' : B₁.toSet = B₂.toSet :=
        Set.translate_inj x _ _ ((hf_spec B₁ hB₁).1.symm.trans ((congr_arg Box.toSet h_eq).trans (hf_spec B₂ hB₂).1))
      -- Since B₁ is in filtered T, it's nonempty, and B₁.toSet = B₂.toSet
      have h_inter_nonempty : (B₁.toSet ∩ B₂.toSet).Nonempty := by
        rw [h_set_eq', Set.inter_self]
        rw [← h_set_eq']
        exact hT_nonempty B₁ hB₁
      rw [Set.pairwiseDisjoint_iff] at hT_disj
      exact hT_disj hB₁ hB₂ h_inter_nonempty
    -- Step 4: Show T' is pairwise disjoint
    have hT'_disj : T'.toSet.PairwiseDisjoint Box.toSet := by
      rw [Set.pairwiseDisjoint_iff]
      intro B₁' hB₁' B₂' hB₂' hB₁'B₂'
      simp [T'] at hB₁' hB₂'
      obtain ⟨B₁, hB₁, rfl⟩ := hB₁'
      obtain ⟨B₂, hB₂, rfl⟩ := hB₂'
      by_cases h_eq : f B₁ = f B₂
      · exact h_eq
      · -- If f B₁ ≠ f B₂ but they intersect, then B₁ = B₂ (contradiction)
        have h_translate_inter : (f B₁).toSet ∩ (f B₂).toSet = (B₁.toSet ∩ B₂.toSet) + {x} := by
          rw [(hf_spec B₁ hB₁).1, (hf_spec B₂ hB₂).1]
          ext y; simp only [Set.mem_inter_iff, Set.mem_add]
          constructor
          · rintro ⟨⟨a₁, ha₁, b₁, hb₁, hab₁⟩, ⟨a₂, ha₂, b₂, hb₂, hab₂⟩⟩
            have hb₁_eq : b₁ = x := Set.mem_singleton_iff.mp hb₁
            have hb₂_eq : b₂ = x := Set.mem_singleton_iff.mp hb₂
            rw [hb₁_eq] at hab₁
            rw [hb₂_eq] at hab₂
            exact ⟨a₁, ⟨ha₁, add_right_cancel (hab₁.trans hab₂.symm) ▸ ha₂⟩, x, Set.mem_singleton x, hab₁⟩
          · rintro ⟨a, ⟨ha₁, ha₂⟩, b, hb, hab⟩
            rw [Set.mem_singleton_iff.mp hb] at hab
            exact ⟨⟨a, ha₁, x, Set.mem_singleton x, hab⟩, ⟨a, ha₂, x, Set.mem_singleton x, hab⟩⟩
        have h_B_nonempty : (B₁.toSet ∩ B₂.toSet).Nonempty := by
          rw [h_translate_inter] at hB₁'B₂'
          obtain ⟨y, hy⟩ := hB₁'B₂'
          obtain ⟨a, ha, b, hb, hab⟩ := Set.mem_add.mp hy
          exact ⟨a, ha.1, ha.2⟩
        rw [Set.pairwiseDisjoint_iff] at hT_disj
        exact (h_eq (congr_arg f (hT_disj hB₁ hB₂ h_B_nonempty))).elim
    -- Step 5: Show E + {x} = ⋃ B' ∈ T', B'.toSet
    have h_union_eq : E + {x} = ⋃ B' ∈ T', B'.toSet := by
      rw [hE_eq]
      ext y; simp
      constructor
      · rintro ⟨B, hB, hy⟩
        use f B, Finset.mem_image.mpr ⟨B, hB, rfl⟩
        rw [(hf_spec B hB).1]
        exact ⟨y + -x, hy, x, Set.mem_singleton x, by simp [add_assoc, add_zero]⟩
      · rintro ⟨B', hB', hy⟩
        obtain ⟨B, hB, rfl⟩ := Finset.mem_image.mp hB'
        rw [(hf_spec B hB).1] at hy
        obtain ⟨a, ha, b, hb, hab⟩ := Set.mem_add.mp hy
        rw [Set.mem_singleton_iff.mp hb] at hab
        exact ⟨B, hB, by rw [← hab]; simp [add_assoc, add_neg_cancel, add_zero]; exact ha⟩
    -- Step 6: Apply measure_eq and show sum equality
    have h_translate_measure : (hE.translate x).measure = ∑ B' ∈ T', |B'|ᵥ :=
      (hE.translate x).measure_eq hT'_disj h_union_eq
    have h_sum_eq : ∑ B' ∈ T', |B'|ᵥ = ∑ B ∈ T, |B|ᵥ := by
      rw [Finset.sum_image (fun B₁ hB₁ B₂ hB₂ h_eq => hf_inj B₁ B₂ hB₁ hB₂ h_eq)]
      exact Finset.sum_congr rfl fun B hB => (hf_spec B hB).2
    rw [h_translate_measure, h_sum_eq, hE.measure_eq hT_disj hE_eq]