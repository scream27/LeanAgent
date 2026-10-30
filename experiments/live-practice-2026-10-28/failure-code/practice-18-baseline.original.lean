/-- The measure of a finite union of boxes (indexed by finset membership) is at most the sum of volumes.
    This is finite subadditivity specialized to boxes with a finset index. -/
lemma measure_le_finset_boxes_volume' {d : ℕ} (t : Finset ℕ) (B : ℕ → Box d) :
    (IsElementary.iUnion_boxes (fun (n : { n // n ∈ t }) => B n.1)).measure ≤ ∑ n ∈ t, (B n).volume := by
  classical
  -- Convert to the Finset of sets form and use IsElementary.measure_of_union'
  haveI : DecidableEq (Set (EuclideanSpace' d)) := Classical.decEq _
  let S_sets : Finset (Set (EuclideanSpace' d)) := t.image (fun n => (B n).toSet)
  have hS_elem : ∀ E ∈ S_sets, IsElementary E := by
    intro E hE
    obtain ⟨n, _, rfl⟩ := Finset.mem_image.mp hE
    exact IsElementary.box (B n)
  -- The subtype union equals the union over S_sets
  have h_union_eq : ⋃ (n : { n // n ∈ t }), (B n.1).toSet = ⋃ E ∈ S_sets, E := by
    ext x
    simp only [Set.mem_iUnion, S_sets]
    constructor
    · intro ⟨⟨n, hn⟩, hx⟩
      exact ⟨(B n).toSet, Finset.mem_image.mpr ⟨n, hn, rfl⟩, hx⟩
    · intro ⟨E, hE_mem, hx⟩
      obtain ⟨n, hn, rfl⟩ := Finset.mem_image.mp hE_mem
      exact ⟨⟨n, hn⟩, hx⟩
  -- Apply measure_eq_of_set_eq to link the elementary witnesses
  have h_measure_eq : (IsElementary.iUnion_boxes (fun (n : { n // n ∈ t }) => B n.1)).measure =
      (IsElementary.union' hS_elem).measure :=
    IsElementary.measure_eq_of_set_eq _ _ h_union_eq
  rw [h_measure_eq]
  -- Apply finite subadditivity from IsElementary.measure_of_union'
  have h_sub := IsElementary.measure_of_union' hS_elem
  -- Reindex the sum: need to show ∑ E : S_sets, (hS_elem E _).measure ≤ ∑ n ∈ t, (B n).volume
  calc (IsElementary.union' hS_elem).measure
      ≤ ∑ E : S_sets, (hS_elem E.val E.property).measure := h_sub
    _ ≤ ∑ n ∈ t, (B n).volume := by
        -- Each elementary measure = box volume, and S_sets.image is subset of t
        -- Use sum over image ≤ sum over domain
        have h_term_eq : ∀ (E : { E // E ∈ S_sets }),
            (hS_elem E.1 E.2).measure = (B (Finset.mem_image.mp E.2).choose).volume := by
          intro ⟨E, hE⟩
          -- choose_spec gives (choose ∈ t ∧ (B choose).toSet = E)
          have h_spec := (Finset.mem_image.mp hE).choose_spec
          let n := (Finset.mem_image.mp hE).choose
          have h_eq : (B n).toSet = E := h_spec.2
          have hB_elem := IsElementary.box (B n)
          have hE_eq : E = (B n).toSet := h_eq.symm
          -- Goal: (hS_elem E hE).measure = (B n).volume
          rw [IsElementary.measure_eq_of_set_eq (hS_elem E hE) hB_elem hE_eq]
          rw [IsElementary.measure_of_box (B n)]
        -- The preimages are a subset of t, so sum ≤ sum over t
        -- Build preimage function: for each E ∈ S_sets, pick n ∈ t such that (B n).toSet = E
        let f : { E // E ∈ S_sets } → ℕ := fun E => (Finset.mem_image.mp E.2).choose
        have hf_mem : ∀ E, f E ∈ t := fun ⟨E, hE⟩ =>
          (Finset.mem_image.mp hE).choose_spec.1
        have hf_eq : ∀ E, (B (f E)).toSet = E.1 := fun ⟨E, hE⟩ =>
          (Finset.mem_image.mp hE).choose_spec.2
        -- Show that f is injective (different sets → different indices via chosen representatives)
        have hf_inj : Function.Injective f := by
          intro ⟨E₁, hE₁⟩ ⟨E₂, hE₂⟩ h_eq
          apply Subtype.ext
          calc E₁ = (B (f ⟨E₁, hE₁⟩)).toSet := (hf_eq ⟨E₁, hE₁⟩).symm
            _ = (B (f ⟨E₂, hE₂⟩)).toSet := by rw [h_eq]
            _ = E₂ := hf_eq ⟨E₂, hE₂⟩
        -- The image of f is a subset of t
        have h_image_sub : (Finset.univ : Finset { E // E ∈ S_sets }).image f ⊆ t := by
          intro n hn
          simp only [Finset.mem_image, Finset.mem_univ, true_and] at hn
          obtain ⟨E, rfl⟩ := hn
          exact hf_mem E
        -- Use Finset.sum_image with injectivity
        calc ∑ E : S_sets, (hS_elem E.val E.property).measure
            = ∑ E : S_sets, (B (f E)).volume := Finset.sum_congr rfl (fun E _ => h_term_eq E)
          _ = ∑ n ∈ (Finset.univ : Finset { E // E ∈ S_sets }).image f, (B n).volume := by
              rw [Finset.sum_image (fun E₁ _ E₂ _ h => hf_inj h)]
          _ ≤ ∑ n ∈ t, (B n).volume :=
              Finset.sum_le_sum_of_subset_of_nonneg h_image_sub
                (fun n _ _ => Box.volume_nonneg (B n))