theorem putnam_1964_a4
(u : ℕ → ℤ)
(boundedu : ∃ B T : ℤ, ∀ n : ℕ, B ≤ u n ∧ u n ≤ T)
(hu : ∀ n ≥ 4, u n = ((u (n - 1) + u (n - 2) + u (n - 3) * u (n - 4)) : ℝ) / (u (n - 1) * u (n - 2) + u (n - 3) + u (n - 4)) ∧ (u (n - 1) * u (n - 2) + u (n - 3) + u (n - 4)) ≠ 0)
: (∃ N c : ℕ, c > 0 ∧ ∀ n ≥ N, u (n + c) = u n) := by
  obtain ⟨B, T, hB⟩ := boundedu
  let f : ℕ → (Fin 4 → Set.Icc B T) := fun n k => ⟨u (n + k), hB (n + k)⟩
  obtain ⟨i, j, hij, he⟩ := Set.finite_univ.exists_lt_map_eq_of_forall_mem
    (f := f) (fun _ => Set.mem_univ _)
  have hp (m : ℕ) : u (i + m) = u (j + m) := by
    induction m using Nat.strong_induction_on with
    | h m ih =>
      by_cases hm : m < 4
      · exact congrArg Subtype.val (congrFun he ⟨m, hm⟩)
      · have hprev (k : ℕ) (hk : 0 < k ∧ k ≤ m) :
            u (i + m - k) = u (j + m - k) := by
          simpa only [Nat.add_sub_assoc hk.2] using ih (m - k) (by omega)
        apply @Int.cast_injective ℝ _ _
        rw [(hu (i + m) (by omega)).1, (hu (j + m) (by omega)).1,
          hprev 1, hprev 2, hprev 3, hprev 4] <;> omega
  refine ⟨i, j - i, by omega, ?_⟩
  intro n hn
  convert (hp (n - i)).symm using 1 <;> congr 1 <;> omega
