theorem putnam_1964_a4
(u : ℕ → ℤ)
(boundedu : ∃ B T : ℤ, ∀ n : ℕ, B ≤ u n ∧ u n ≤ T)
(hu : ∀ n ≥ 4, u n = ((u (n - 1) + u (n - 2) + u (n - 3) * u (n - 4)) : ℝ) / (u (n - 1) * u (n - 2) + u (n - 3) + u (n - 4)) ∧ (u (n - 1) * u (n - 2) + u (n - 3) + u (n - 4)) ≠ 0)
: (∃ N c : ℕ, c > 0 ∧ ∀ n ≥ N, u (n + c) = u n) := by
  classical
  obtain ⟨B, T, hB⟩ := boundedu
  let f := fun n (k : Fin 4) => (⟨u (n + k), hB (n + k)⟩ : Set.Icc B T)
  obtain ⟨a, b, hab, he⟩ := Set.finite_univ.exists_lt_map_eq_of_forall_mem
    (f := f) (fun _ => Set.mem_univ _)
  have hp (m : ℕ) : u (a + m) = u (b + m) := by
    induction m using Nat.strong_induction_on with
    | h m ih =>
      by_cases hm : m < 4
      · exact congrArg Subtype.val (congrFun he ⟨m, hm⟩)
      · have h (k : ℕ) (hk : 0 < k ∧ k ≤ 4) : u (a + m - k) = u (b + m - k) := by
          simpa only [Nat.add_sub_assoc (show k ≤ m by omega)] using ih (m-k) (by omega)
        apply Int.cast_injective (α := ℝ)
        rw [(hu (a+m) (by omega)).1, (hu (b+m) (by omega)).1,
          h 1 (by decide), h 2 (by decide), h 3 (by decide), h 4 (by decide)]
  refine ⟨a, b-a, by omega, fun n hn => ?_⟩
  convert (hp (n-a)).symm using 1 <;> congr 1 <;> omega
