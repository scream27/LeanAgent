theorem putnam_1964_b2
(S : Type*) [Fintype S] [Nonempty S]
(P : Finset (Set S))
(hPP : ∀ T ∈ P, ∀ U ∈ P, T ∩ U ≠ ∅)
(hPS : ¬∃ T : Set S, T ∉ P ∧ (∀ U ∈ P, T ∩ U ≠ ∅))
: (P.card = 2 ^ (Fintype.card S - 1)) := by
  classical
  have hi : (P : Set (Set S)).Intersecting := by
    simpa only [Set.Intersecting, Set.disjoint_iff_inter_eq_empty, Finset.mem_coe] using hPP
  have hc := hi.is_max_iff_card_eq.mp (by
    intro Q hQ hPQ
    apply Finset.Subset.antisymm hPQ
    intro T hT
    by_contra hn
    exact hPS ⟨T, hn, fun U hU => by
      simpa only [Set.disjoint_iff_inter_eq_empty] using hQ hT (hPQ hU)⟩)
  rw [Fintype.card_set] at hc
  have hp := Nat.sub_add_cancel (Fintype.card_pos (α := S))
  have he : 2 ^ (Fintype.card S - 1) * 2 = 2 ^ Fintype.card S := by
    rw [← pow_succ, hp]
  omega
