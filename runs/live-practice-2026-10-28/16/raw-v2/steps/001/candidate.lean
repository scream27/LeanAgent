/-- When d > 0, the Lebesgue outer measure can be computed using ℕ-indexed box sequences,
    which is equivalent to the definition using countable families. This is because we can
    pad any countable family with zero-volume boxes (which exist when d > 0). -/
lemma Lebesgue_outer_measure_eq_nat_indexed {d:ℕ} (hd: 0 < d) (E: Set (EuclideanSpace' d)) :
    Lebesgue_outer_measure E =
    sInf (((fun S: ℕ → Box d ↦ ∑' n, (S n).volume.toEReal)) '' { S | E ⊆ ⋃ n, (S n).toSet }) := by
  unfold Lebesgue_outer_measure
  -- Strategy: Show both ≤ directions
  -- (≤): Any ℕ-indexed cover is a countable cover with X = Set.univ
  -- (≥): For any countable cover (X, S), construct ℕ-indexed S' by:
  --      - Use the equivalence Set.univ ≃ ℕ to reindex
  --      - Show sums are equal via Equiv.tsum_eq
  apply le_antisymm

  -- Part 1 (≤): ℕ-indexed covers ≥ countable covers
  · apply le_sInf
    intro b hb
    obtain ⟨S, hS_cover, rfl⟩ := hb
    -- Show ∑' n, (S n).volume.toEReal is in the countable covers set
    apply sInf_le
    show ∑' n, (S n).volume.toEReal ∈ { V | ∃ (X : Set ℕ) (S: X → Box d), E ⊆ ⋃ n, (S n).toSet ∧ V = ∑' n, (S n).volume.toEReal }
    -- Convert S : ℕ → Box d to S' : Set.univ → Box d
    let S' : Set.univ → Box d := fun n => S n.val
    use Set.univ, S'
    constructor
    · -- Covering property: E ⊆ ⋃ n : Set.univ, (S' n).toSet
      have : (⋃ n : Set.univ, (S' n).toSet) = (⋃ n, (S n).toSet) := by
        ext x
        simp [S']
      rw [this]
      exact hS_cover
    · -- Sum equality: ∑' (n : Set.univ), (S' n).volume.toEReal = ∑' n, (S n).volume.toEReal
      -- Strategy: Use Equiv.tsum_eq to reindex from Set.univ to ℕ
      simp only [S']
      -- The equivalence Equiv.Set.univ : Set.univ ≃ ℕ allows us to reindex the sum
      -- We want: ∑' (n : Set.univ), f(n.val) = ∑' (n : ℕ), f(n)
      -- Equiv.tsum_eq gives: ∑' (c : Set.univ), f(e c) = ∑' (b : ℕ), f b
      -- We need to apply it backwards (using symm)
      exact ((Equiv.Set.univ ℕ).tsum_eq (fun n => (S n).volume.toEReal)).symm

  -- Part 2 (≥): Countable covers ≥ ℕ-indexed covers
  · apply le_sInf
    intro b hb
    simp only [Set.mem_setOf_eq] at hb
    obtain ⟨X, S, hS_cover, hb_eq⟩ := hb
    open Classical in

    -- Construct zero-volume box (exists when d > 0)
    have ⟨B₀, hB₀⟩ : ∃ B : Box d, B.volume = 0 := by
      -- When d > 0, we can construct a box with empty interval in first dimension
      use ⟨fun i => BoundedInterval.Ioc 0 0⟩
      simp only [Box.volume, BoundedInterval.length]
      -- The product ∏ i : Fin d, max (0 - 0) 0 = ∏ i : Fin d, 0
      conv_lhs => arg 2; ext i; rw [sub_self, max_eq_right (le_refl 0)]
      -- Now we have ∏ i : Fin d, 0 = 0^d (since d > 0, this is 0)
      rw [Finset.prod_const]
      rw [show Finset.univ.card = d from Fintype.card_fin d]
      exact zero_pow (Nat.pos_iff_ne_zero.mp hd)

    -- Extend S : X → Box d to S' : ℕ → Box d by using B₀ for indices not in X
    let S' : ℕ → Box d := fun n => if h : n ∈ X then S ⟨n, h⟩ else B₀

    -- Show S' is a valid cover
    have hS'_cover : E ⊆ ⋃ n, (S' n).toSet := by
      intro x hx
      rcases Set.mem_iUnion.mp (hS_cover hx) with ⟨⟨n, hn⟩, hxn⟩
      exact Set.mem_iUnion.mpr ⟨n, by simpa [S', hn] using hxn⟩

    -- Show sums are equal
    have h_sum : ∑' n, (S' n).volume.toEReal = ∑' (n : X), (S n).volume.toEReal := by
      -- Strategy: Rewrite S' using if-then-else, then show terms outside X contribute 0
      -- Use tsum_congr to match terms inside X with the subtype sum

      -- Step 1: Express the LHS explicitly showing the if-then-else
      have h_S'_eq : ∀ n, (S' n).volume.toEReal =
          if h : n ∈ X then (S ⟨n, h⟩).volume.toEReal else (B₀.volume : EReal) := by
        intro n
        simp only [S']
        split_ifs <;> rfl

      simp_rw [h_S'_eq, hB₀]
      simp only [EReal.coe_zero]

      -- Step 2: The sum ∑' n, (if n ∈ X then f n else 0) = ∑' (n : X), f n
      -- This is the key equality relating the full sum to the subtype sum
      -- Strategy: Show both sums enumerate the same terms via subtype coercion

      -- Both sides sum over the same elements: for each n ∈ X, we add (S n).volume
      -- The LHS uses characteristic function; RHS uses subtype indexing
      -- This is a standard reindexing via the subtype embedding coe : X → ℕ

      -- Show the functions match when properly aligned

      -- Now we need: ∑' n : ℕ, (if h : n ∈ X then ... else 0) = ∑' x : X, f x
      -- This is a standard measure theory fact: summing with characteristic function
      -- equals summing over the subtype. Both sums enumerate exactly the same terms

      -- Define g to make the terms clearer
      let g : ℕ → EReal := fun n => if h : n ∈ X then (S ⟨n, h⟩).volume.toEReal else 0

      -- 1. Show LHS equals sum of g
      have h1 : (∑' n, if h : n ∈ X then (S ⟨n, h⟩).volume.toEReal else 0) = ∑' n, g n := rfl

      -- 2. Use tsum_subtype to relate sum over ℕ to sum over X
      have h2 : ∑' n, g n = ∑' (x : X), g x := by
        -- Use classical logic for if-then-else
        classical
        -- tsum_subtype gives: ∑' x:X, f x = ∑' n, if n ∈ X then f n else 0
        -- We rewrite the RHS (sum over X) to sum over ℕ with if-then-else
        rw [tsum_subtype (f := g)]
        -- Now we match the sums term by term
        apply tsum_congr
        intro n
        -- g n is defined exactly to be 0 outside X, matching the if-then-else
        rw [Set.indicator_apply]
        split_ifs with h
        · rfl
        · simp [g, h]

      -- 3. Show g restricted to X equals the RHS term
      have h3 : ∑' (x : X), g x = ∑' (x : X), (S x).volume.toEReal := by
        apply tsum_congr
        intro x
        -- For x ∈ X, g x simplifies to S x.volume
        simp [g, x.property]

      -- Combine steps
      rw [h1, h2, h3]

    -- Apply sInf_le
    calc sInf (((fun S: ℕ → Box d ↦ ∑' n, (S n).volume.toEReal)) '' { S | E ⊆ ⋃ n, (S n).toSet })
        ≤ ∑' n, (S' n).volume.toEReal := by
            apply sInf_le
            use S', hS'_cover
        _ = ∑' (n : X), (S n).volume.toEReal := h_sum
        _ = b := hb_eq.symm
