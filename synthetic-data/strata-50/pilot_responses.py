"""Raw first responses authored by the Codex session before pilot verification.

This file is a transport envelope, not a procedural proof mutation generator.
The strings below are the complete generated proof terms.
"""
RESPONSES = {
'Nat_toDigitsCore_list_head_eq': [
'''by
  intro H
  have hleft : h1 :: t <:+ Nat.toDigitsCore 10 x n (h1 :: t) := Nat_toDigitsCore_list_suffix
  have hright : h2 :: t <:+ Nat.toDigitsCore 10 y m (h2 :: t) := Nat_toDigitsCore_list_suffix
  rw [H] at hleft
  have hs := List.suffix_of_suffix_length_le hleft hright (by simp)
  simpa [List.suffix_iff_eq_drop] using hs''',
'''by
  intro H
  have hs : h1 :: t <:+ h2 :: t := List.suffix_of_suffix_length_le
    (H ▸ (Nat_toDigitsCore_list_suffix (x := x) (n := n) (l := h1 :: t)))
    (Nat_toDigitsCore_list_suffix (x := y) (n := m) (l := h2 :: t)) (by simp)
  simpa [List.suffix_iff_eq_drop] using hs''',
'''by
  intro H
  have hleft := Nat_toDigitsCore_list_suffix (x := x) (n := n) (l := h1 :: t)
  have hright := Nat_toDigitsCore_list_suffix (x := y) (n := m) (l := h2 :: t)
  rw [H] at hleft
  have hs : h1 :: t <:+ h2 :: t := List.suffix_of_suffix_length_le hleft hright (by simp)
  simp_all [List.suffix_iff_eq_drop]''',
'''by
  intro H
  have a : h1 :: t <:+ Nat.toDigitsCore 10 y m (h2 :: t) := by
    rw [← H]
    exact Nat_toDigitsCore_list_suffix
  have b : h2 :: t <:+ Nat.toDigitsCore 10 y m (h2 :: t) := Nat_toDigitsCore_list_suffix
  have c : h1 :: t <:+ h2 :: t := List.suffix_of_suffix_length_le a b (by simp)
  have e : h1 :: t = h2 :: t := by simpa [List.suffix_iff_eq_drop] using c
  exact (List.cons.inj e).1''',
'''by
  intro H
  have a := Nat_toDigitsCore_list_suffix (x := x) (n := n) (l := h1 :: t)
  have b := Nat_toDigitsCore_list_suffix (x := y) (n := m) (l := h2 :: t)
  rw [H] at a
  have c := List.suffix_of_suffix_length_le a b (by simp)
  simpa [List.suffix_iff_eq_drop] using c''',
],
'Core.Factory_wf': [
'''by
  unfold Factory
  constructor
  · decide
  · unfold HAppend.hAppend Array.instHAppendList Array.appendList
    simp only [List.foldl, Array.push, List.concat]
    intro lf
    rw [← Array.mem_toList_iff]
    intro Hmem
    repeat (
      rcases Hmem with _ | ⟨a', Hmem⟩
      · constructor
        · decide
        · decide
        · simp (config := { ground := true })
          try (
            try unfold unOpCeval
            try unfold binOpCeval
            try unfold cevalIntDiv
            try unfold cevalIntMod
            try unfold bvUnaryOp
            try unfold bvBinaryOp
            try unfold bvShiftOp
            try unfold bvBinaryPred
            intros lf md args res
            repeat (rcases args with _ | ⟨args0, args⟩ <;> try grind)))
    contradiction''',
'''by
  unfold Factory
  refine ⟨by decide, ?_⟩
  unfold HAppend.hAppend Array.instHAppendList Array.appendList
  simp only [List.foldl, Array.push, List.concat]
  intro lf
  rw [← Array.mem_toList_iff]
  intro Hmem
  repeat (
    rcases Hmem with _ | ⟨a', Hmem⟩
    · refine ⟨by decide, by decide, ?_⟩
      simp (config := { ground := true })
      try (
        simp only [unOpCeval, binOpCeval, cevalIntDiv, cevalIntMod,
          bvUnaryOp, bvBinaryOp, bvShiftOp, bvBinaryPred]
        intros lf md args res
        repeat (rcases args with _ | ⟨args0, args⟩ <;> try grind)))
  contradiction''',
'''by
  unfold Factory
  constructor
  · decide
  · unfold HAppend.hAppend Array.instHAppendList Array.appendList
    simp only [List.foldl, Array.push, List.concat]
    intro lf
    rw [← Array.mem_toList_iff]
    intro Hmem
    repeat (
      rcases Hmem with _ | ⟨a', Hmem⟩
      · constructor
        · decide
        · decide
        · simp (config := { ground := true })
          try (
            repeat first | unfold unOpCeval | unfold binOpCeval
              | unfold cevalIntDiv | unfold cevalIntMod | unfold bvUnaryOp
              | unfold bvBinaryOp | unfold bvShiftOp | unfold bvBinaryPred
            intros lf md args res
            repeat (rcases args with _ | ⟨args0, args⟩ <;> try grind)))
    contradiction''',
'''by
  unfold Factory
  apply FactoryWF.mk
  · decide
  · unfold HAppend.hAppend Array.instHAppendList Array.appendList
    simp only [List.foldl, Array.push, List.concat]
    intros lf
    rw [← Array.mem_toList_iff]
    intros Hmem
    repeat (
      rcases Hmem with _ | ⟨a', Hmem⟩
      · apply LFuncWF.mk
        · decide
        · decide
        · simp (config := { ground := true })
          try (
            try unfold unOpCeval
            try unfold binOpCeval
            try unfold cevalIntDiv
            try unfold cevalIntMod
            try unfold bvUnaryOp
            try unfold bvBinaryOp
            try unfold bvShiftOp
            try unfold bvBinaryPred
            intros lf md args res
            repeat (rcases args with _ | ⟨args0, args⟩ <;> try grind)))
    contradiction''',
'''by
  unfold Factory
  constructor
  · decide
  · unfold HAppend.hAppend Array.instHAppendList Array.appendList
    simp only [List.foldl, Array.push, List.concat]
    intro lf
    rw [← Array.mem_toList_iff]
    intro Hmem
    repeat (
      rcases Hmem with _ | ⟨a', Hmem⟩
      · constructor
        · decide
        · decide
        · simp (config := { ground := true })
          try (
            simp only [unOpCeval, binOpCeval, cevalIntDiv, cevalIntMod,
              bvUnaryOp, bvBinaryOp, bvShiftOp, bvBinaryPred]
            intros lf md args res
            repeat (rcases args with _ | ⟨args0, args⟩ <;> try grind)))
    contradiction''',
],
'loop_middle_nodup': [
'''by
  intros α h t l l' inst inst2 H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil =>
    apply nodup_swap
    simp
    apply nodup_middle'
    rw [← List.cons_append]
    exact nodup_swap H
  case cons h' t ih =>
    by_cases Heq : h' == h
    · rw [eq_of_beq Heq] at H ⊢
      simp at H
      by_cases hh : h ∈ l
      · simp; exact ih H
      · split
        · exact ih H
        · simp_all
    · split
      · simp_all
        apply ih
        split at H <;> simp_all
        grind
      · simp_all
        change (List.eraseDupsBy.loop (· == ·) t ((h' :: [h]) ++ (l' ++ l))).Nodup
        apply ih
        simp
        change (List.eraseDupsBy.loop (· == ·) t (h :: ((h' :: l') ++ l))).Nodup
        apply ih
        simp
        grind''',
'''by
  intros α h t l l' inst inst2 H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil =>
    apply nodup_swap
    simp
    apply nodup_middle'
    rw [← List.cons_append]
    exact nodup_swap H
  case cons a t ih =>
    by_cases he : a == h
    · rw [eq_of_beq he] at H ⊢
      simp at H
      by_cases hh : h ∈ l <;> simp_all
      split <;> simp_all
      exact ih H
    · split <;> simp_all
      · apply ih
        split at H <;> simp_all
        grind
      · apply ih (l' := a :: l')
        simp_all
        grind''',
'''by
  intros α h t l l' inst inst2 H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil =>
    apply nodup_swap
    simp
    apply nodup_middle'
    rw [← List.cons_append]
    exact nodup_swap H
  case cons a t ih =>
    by_cases he : a == h
    · rw [eq_of_beq he] at H ⊢
      simp at H
      by_cases hh : h ∈ l
      · simp; exact ih H
      · split <;> first | exact ih H | simp_all
    · split
      · simp_all
        apply ih
        split at H <;> simp_all
        grind
      · simp_all
        have e₁ : a :: h :: (l' ++ l) = (a :: [h]) ++ (l' ++ l) := rfl
        rw [e₁]
        apply ih
        simp
        have e₂ : h :: a :: (l' ++ l) = h :: ((a :: l') ++ l) := rfl
        rw [e₂]
        apply ih
        simp
        grind''',
'''by
  intros α h t l l' inst inst2 H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil =>
    apply nodup_swap
    simp
    apply nodup_middle'
    rw [← List.cons_append]
    exact nodup_swap H
  case cons a t ih =>
    by_cases he : a == h
    · rw [eq_of_beq he] at H ⊢
      simp at H
      by_cases hh : h ∈ l
      · simp; exact ih H
      · split
        · exact ih H
        · simp_all
    · split
      · simp_all
        apply ih
        split at H <;> simp_all
        grind
      · simp_all
        have e₁ : a :: h :: (l' ++ l) = (a :: [h]) ++ (l' ++ l) := rfl
        rw [e₁]
        apply ih; simp
        have e₂ : h :: a :: (l' ++ l) = h :: ((a :: l') ++ l) := rfl
        rw [e₂]
        apply ih; simp
        grind''',
'''by
  intros α h t l l' inst inst2 H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil =>
    apply nodup_swap
    simp
    apply nodup_middle'
    rw [← List.cons_append]
    exact nodup_swap H
  case cons a t ih =>
    by_cases he : a == h
    · rw [eq_of_beq he] at H ⊢
      simp at H
      by_cases hh : h ∈ l
      · simp; exact ih H
      · split <;> first | exact ih H | simp_all
    · split <;> simp_all
      · apply ih
        split at H <;> simp_all
        grind
      · grind''',
],
}
