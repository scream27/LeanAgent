theorem putnam_1995_a3
(relation : (Fin 9 → ℤ) → (Fin 9 → ℤ) → Prop)
(digits_to_num : (Fin 9 → ℤ) → ℤ)
(hdigits_to_num : digits_to_num = fun dig => ∑ i : Fin 9, (dig i) * 10^i.1)
(hrelation : ∀ d e : (Fin 9 → ℤ), relation d e ↔ (∀ i : Fin 9, d i < 10 ∧ d i ≥ 0 ∧ e i < 10 ∧ e i ≥ 0) ∧ (∀ i : Fin 9, 7 ∣ (digits_to_num (fun j : Fin 9 => if j = i then e j else d j))))
: ∀ d e f : (Fin 9 → ℤ), ((relation d e) ∧ (relation e f)) → (∀ i : Fin 9, 7 ∣ d i - f i) := by
  classical
  have rep (a b : Fin 9 → ℤ) (i : Fin 9) :
      digits_to_num (fun j => if j = i then b j else a j) =
        digits_to_num a + (b i - a i) * 10^i.1 := by
    rw [← sub_eq_iff_eq_add']
    simp only [hdigits_to_num, ← Finset.sum_sub_distrib]
    trans ∑ j : Fin 9, if j = i then (b i-a i)*10^i.1 else 0
    · apply Finset.sum_congr rfl
      intro j _
      by_cases h : j = i
      · subst j; simp only [ite_true, sub_mul]
      · simp only [if_neg h, sub_self]
    · simp only [Finset.sum_ite_eq', Finset.mem_univ, if_true]
  intro d e f h
  have hd := fun i => ((hrelation d e).mp h.1).2 i
  have he := fun i => ((hrelation e f).mp h.2).2 i
  simp only [rep] at hd he
  have hs := Finset.dvd_sum (s := Finset.univ) (fun i _ => hd i)
  have ht : (∑ i : Fin 9, (digits_to_num d + (e i-d i)*10^i.1)) =
      7 * digits_to_num d + (digits_to_num d + digits_to_num e) := by
    simp only [sub_mul, Finset.sum_add_distrib, Finset.sum_sub_distrib,
      Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul, Nat.cast_ofNat, hdigits_to_num]
    rw [show (9 : ℤ) = 7+2 from rfl, add_mul, add_assoc, two_mul, add_add_sub_cancel]
  rw [ht] at hs
  have hs := dvd_sub hs (dvd_mul_right 7 (digits_to_num d))
  simp only [add_sub_cancel_left] at hs
  have hc : IsCoprime (7 : ℤ) 10 := ⟨3, -2, by decide⟩
  intro i
  apply (hc.pow_right (n := i.1)).dvd_of_dvd_mul_right
  have hi := dvd_add (hd i) (he i)
  rw [add_add_add_comm, ← add_mul, sub_add_sub_cancel'] at hi
  simpa only [sub_add_eq_sub_sub, sub_self, zero_sub, ← neg_mul, neg_sub] using dvd_sub hs hi
