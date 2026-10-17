"""Complete first responses for the seven remaining references, before verification."""
RESPONSES = {
'Nat_eq_of_StringGen_suffix': [
'''by
  intro hs
  apply Nat_eq_of_toString_eq
  by_cases hlt : (toString x).length < (toString y).length
  · simp only [String.IsSuffix, String.toList_append, under_toList] at hs
    have hy : (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := List.suffix_append_of_suffix (List.suffix_refl _)
    obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hs hy (by simp; exact hlt)
    have hu : '_' ∈ (toString y).toList := by simp [← ht]
    exact False.elim (Nat_toString_not_contain_underscore hu)
  · by_cases hgt : (toString y).length < (toString x).length
    · have hx : (toString x).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
        obtain ⟨t, ht⟩ := hs
        refine ⟨t ++ ['_'], ?_⟩
        simpa only [String.toList_append, under_toList, List.append_assoc] using ht
      have hy : ['_'] ++ (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
        simpa only [List.append_assoc] using List.suffix_append_of_suffix (l₁ := s.toList) (List.suffix_refl (['_'] ++ (toString y).toList))
      obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hy hx (by simp; omega)
      have hu : '_' ∈ (toString x).toList := by simp [← ht]
      exact False.elim (Nat_toString_not_contain_underscore hu)
    · obtain ⟨t, ht⟩ := hs
      simp only [String.toList_append, ← List.append_assoc] at ht
      exact String.toList_inj.mp (List.append_inj_right' ht (by omega))''',
'''by
  intro hs
  apply Nat_eq_of_toString_eq
  have nox := @Nat_toString_not_contain_underscore x
  have noy := @Nat_toString_not_contain_underscore y
  by_cases hlt : (toString x).length < (toString y).length
  · simp only [String.IsSuffix, String.toList_append, under_toList] at hs
    have hy : (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := List.suffix_append_of_suffix (List.suffix_refl _)
    obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hs hy (by simp; exact hlt)
    exact False.elim (noy (by simp [← ht]))
  · by_cases hgt : (toString x).length > (toString y).length
    · have hx : (toString x).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
        obtain ⟨t, ht⟩ := hs
        exists t ++ ['_']
        simp only [String.toList_append, under_toList, List.append_assoc] at ht
        simpa only [List.append_assoc] using ht
      have hy : ['_'] ++ (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
        simp only [List.append_assoc]
        exact List.suffix_append_of_suffix (List.suffix_refl _)
      obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hy hx (by simp; omega)
      exact False.elim (nox (by simp [← ht]))
    · obtain ⟨t, ht⟩ := hs
      simp only [String.toList_append, ← List.append_assoc] at ht
      exact String.toList_inj.mp (List.append_inj_right' ht (by omega))''',
'''by
  intro hs
  apply Nat_eq_of_toString_eq
  if hlt : (toString x).length < (toString y).length then
    simp only [String.IsSuffix, String.toList_append, under_toList] at hs
    have hy : (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := List.suffix_append_of_suffix (List.suffix_refl _)
    obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hs hy (by simp; exact hlt)
    have hu : '_' ∈ (toString y).toList := by simp [← ht]
    have := @Nat_toString_not_contain_underscore y
    contradiction
  else if hgt : (toString x).length > (toString y).length then
    have hx : (toString x).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
      obtain ⟨t, ht⟩ := hs
      exists t ++ ['_']
      simp only [String.toList_append, under_toList, List.append_assoc] at ht
      simpa only [List.append_assoc] using ht
    have hy : ['_'] ++ (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
      simp only [List.append_assoc]
      exact List.suffix_append_of_suffix (List.suffix_refl _)
    obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hy hx (by simp; omega)
    have hu : '_' ∈ (toString x).toList := by simp [← ht]
    have := @Nat_toString_not_contain_underscore x
    contradiction
  else
    obtain ⟨cs, ht⟩ := hs
    simp only [String.toList_append, ← List.append_assoc] at ht
    exact String.toList_inj.mp (List.append_inj_right' ht (by omega))''',
'''by
  intro hs
  apply Nat_eq_of_toString_eq
  have hx : (toString x).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
    obtain ⟨t, ht⟩ := hs
    refine ⟨t ++ ['_'], ?_⟩
    simpa only [String.toList_append, under_toList, List.append_assoc] using ht
  have hy : (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := List.suffix_append_of_suffix (List.suffix_refl _)
  have hyu : ['_'] ++ (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
    simp only [List.append_assoc]
    exact List.suffix_append_of_suffix (List.suffix_refl _)
  have hxu : ['_'] ++ (toString x).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
    simpa only [String.IsSuffix, String.toList_append, under_toList] using hs
  have he : (toString x).length = (toString y).length := by
    by_contra hn
    rcases Nat.lt_or_gt_of_ne hn with hl | hl
    · obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hxu hy (by simp; omega)
      exact Nat_toString_not_contain_underscore (by simp [← ht])
    · obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hyu hx (by simp; omega)
      exact Nat_toString_not_contain_underscore (by simp [← ht])
  exact String.toList_inj.mp ((List.suffix_of_suffix_length_le hx hy (by simpa using Nat.le_of_eq he)).eq_of_length_le (by simpa using Nat.le_of_eq he.symm))''',
'''by
  intro hs
  apply Nat_eq_of_toString_eq
  by_cases hlt : (toString x).length < (toString y).length
  · simp only [String.IsSuffix, String.toList_append, under_toList] at hs
    have hy : (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := List.suffix_append_of_suffix (List.suffix_refl _)
    obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hs hy (by simp; omega)
    have := @Nat_toString_not_contain_underscore y
    simp [← ht] at this
  · by_cases hgt : (toString x).length > (toString y).length
    · have hx : (toString x).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
        obtain ⟨t, ht⟩ := hs
        exists t ++ ['_']
        simpa only [String.toList_append, under_toList, List.append_assoc] using ht
      have hy : ['_'] ++ (toString y).toList <:+ s.toList ++ ['_'] ++ (toString y).toList := by
        simp only [List.append_assoc]
        exact List.suffix_append_of_suffix (List.suffix_refl _)
      obtain ⟨t, ht⟩ := List.suffix_of_suffix_length_le hy hx (by simp; omega)
      have := @Nat_toString_not_contain_underscore x
      simp [← ht] at this
    · obtain ⟨cs, ht⟩ := hs
      simp only [String.toList_append, ← List.append_assoc] at ht
      exact String.toList_inj.mp (List.append_inj_right' ht (by omega))''',
],
'List.length_dedup_of_all_in_not_mem_lt': [
'''by
  have hmem : (a :: l₁).all (fun e => e ∈ l₂) := by simp_all
  have hle := length_dedup_append_le_left (a :: l₁) l₂
  rw [length_dedup_append_all_in_right (a :: l₁) l₂ hmem] at hle
  rw [length_dedup_cons_of_not_mem a l₁ h2] at hle
  omega''',
'''by
  have hmem : (a :: l₁).all (fun e => e ∈ l₂) := by simp [h1, h3]
  have hle : (a :: l₁).dedup.length ≤ l₂.dedup.length := by
    simpa only [length_dedup_append_all_in_right (a :: l₁) l₂ hmem] using length_dedup_append_le_left (a :: l₁) l₂
  have hlen := length_dedup_cons_of_not_mem a l₁ h2
  omega''',
'''by
  have hc := length_dedup_cons_of_not_mem a l₁ h2
  have hb := length_dedup_append_le_left (a :: l₁) l₂
  have he := length_dedup_append_all_in_right (a :: l₁) l₂ (by simp_all)
  omega''',
'''by
  have hmem : (a :: l₁).all (fun e => e ∈ l₂) := by simp_all
  have hle : 1 + l₁.dedup.length ≤ l₂.dedup.length := by
    rw [← length_dedup_cons_of_not_mem a l₁ h2, ← length_dedup_append_all_in_right (a :: l₁) l₂ hmem]
    exact length_dedup_append_le_left (a :: l₁) l₂
  omega''',
'''by
  have hle := length_dedup_append_le_left (a :: l₁) l₂
  have he := length_dedup_append_all_in_right (a :: l₁) l₂ (by simp_all)
  simp only [length_dedup_cons_of_not_mem a l₁ h2] at hle
  omega''',
],
'loop_insert_nodup': [
'''by
  intros α h t l l' inst inst2 Hnotin1 Hnotin2 Hnodup
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil => exact nodup_insert α (not_in_reverse.mp Hnotin2) (not_in_reverse.mp Hnotin1) Hnodup
  case cons h' t ih =>
    split at Hnodup
    · split <;> simp_all
      next x heq =>
      grind
    · split
      · simp_all
        apply ih <;> try assumption
        change (List.eraseDupsBy.loop (· == ·) t ([] ++ (l ++ l'))).Nodup
        apply loop_shrink_nodup <;> assumption
      · simp_all
        change (List.eraseDupsBy.loop (· == ·) t ((h' :: l) ++ h :: l')).Nodup
        apply ih <;> try assumption
        simp_all
        exact fun a => ‹¬ h' = h› (Eq.symm a)''',
'''by
  intros α h t l l' inst inst2 hn hn' H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil => exact nodup_insert α (not_in_reverse.mp hn') (not_in_reverse.mp hn) H
  case cons a t ih =>
    split at H
    · split <;> simp_all
      grind
    · split <;> simp_all
      · apply ih <;> try assumption
        exact loop_shrink_nodup α (l' := []) H
      · apply ih <;> simp_all
        grind''',
'''by
  intros α h t l l' inst inst2 hn hn' H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil =>
    apply nodup_insert
    · exact not_in_reverse.mp hn'
    · exact not_in_reverse.mp hn
    · assumption
  case cons a t ih =>
    split at H
    · split <;> simp_all
      next x he =>
      grind
    · split
      · simp_all
        apply ih <;> try assumption
        have he : l ++ l' = [] ++ (l ++ l') := rfl
        rw [he]
        apply loop_shrink_nodup <;> assumption
      · next x he =>
        simp_all
        have heq : a :: (l ++ h :: l') = (a :: l) ++ h :: l' := rfl
        rw [heq]
        apply ih <;> try assumption
        simp_all
        exact fun e => he (Eq.symm e)''',
'''by
  intros α h t l l' inst inst2 hn hn' H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil => exact nodup_insert α (not_in_reverse.mp hn') (not_in_reverse.mp hn) H
  case cons a t ih =>
    split at H
    next x he =>
      split <;> simp_all
      next x' he' =>
      cases he with
      | inl hin => have hc := he'.1 a hin; simp_all
      | inr hin => have hc := he'.2.2 a hin; simp_all
    next x he =>
      split
      · simp_all
        apply ih <;> try assumption
        change (List.eraseDupsBy.loop (· == ·) t ([] ++ (l ++ l'))).Nodup
        apply loop_shrink_nodup <;> assumption
      · next x' he' =>
        simp_all
        change (List.eraseDupsBy.loop (· == ·) t ((a :: l) ++ h :: l')).Nodup
        apply ih <;> try assumption
        simp_all
        exact fun e => he' (Eq.symm e)''',
'''by
  intros α h t l l' inst inst2 hn hn' H
  induction t generalizing l l' h <;> simp [List.eraseDupsBy.loop] at *
  case nil => exact nodup_insert α (not_in_reverse.mp hn') (not_in_reverse.mp hn) H
  case cons a t ih =>
    split at H <;> split <;> simp_all
    · grind
    · apply ih <;> try assumption
      change (List.eraseDupsBy.loop (· == ·) t ([] ++ (l ++ l'))).Nodup
      apply loop_shrink_nodup <;> assumption
    · apply ih <;> simp_all
      grind''',
],
'Lambda.LMonoTy.subst_keys_not_in_substituted_type': [
'''by
  by_cases he : S.hasEmptyScopes
  · simp_all [Subst.isEmpty_implies_keys_empty S he]
  · induction ty
    case ftvar i =>
      simp_all [LMonoTy.subst]
      intro id hid
      split
      · rename_i sty hs
        simp_all [SubstWF, Subst.freeVars]
        exact h id hid sty (Maps.find?_mem_values hs)
      · simp_all [freeVars]
        have := @Maps.find?_of_not_mem_values _ _ i _ S
        simp_all
        exact ne_of_mem_of_not_mem hid this
    case bitvec n => simp_all [LMonoTy.subst, LMonoTy.freeVars]
    case tcons name args ih =>
      simp_all
      simp [subst]
      induction args
      · simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic, LMonoTys.freeVars, LMonoTy.freeVars]
      · rename_i head tail iht
        simp_all
        obtain ⟨ih1, ih2⟩ := ih
        intro x hx
        have hh := ih1 x hx
        simp [LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic] at iht ⊢
        simp [he, hh]
        exact iht x hx''',
'''by
  by_cases he : S.hasEmptyScopes
  · simp_all [Subst.isEmpty_implies_keys_empty S he]
  · induction ty
    case ftvar i =>
      simp_all [LMonoTy.subst]
      intro id hid
      split
      · rename_i _ sty hs
        simp_all [SubstWF, Subst.freeVars]
        exact h id hid sty (@Maps.find?_mem_values _ _ i sty _ S hs)
      · simp_all [freeVars]
        have := @Maps.find?_of_not_mem_values _ _ i _ S
        simp_all
        exact ne_of_mem_of_not_mem hid this
    case bitvec n => simp_all [LMonoTy.subst, LMonoTy.freeVars]
    case tcons name args ih =>
      simp_all
      simp [subst]
      induction args <;> simp_all [LMonoTy.freeVars, LMonoTys.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]''',
'''by
  by_cases he : S.hasEmptyScopes
  · simp_all [Subst.isEmpty_implies_keys_empty S he]
  · induction ty
    case ftvar i =>
      simp_all [LMonoTy.subst]
      intro id hid
      split
      · rename_i _ sty hs
        simp_all [SubstWF, Subst.freeVars]
        exact h id hid sty (@Maps.find?_mem_values _ _ i sty _ S hs)
      · simp_all [freeVars]
        have := @Maps.find?_of_not_mem_values _ _ i _ S
        simp_all
        exact ne_of_mem_of_not_mem hid this
    case bitvec n => simp_all [LMonoTy.subst, LMonoTy.freeVars]
    case tcons name args ih =>
      simp_all
      simp [subst]
      induction args
      case nil => simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic, LMonoTys.freeVars, LMonoTy.freeVars]
      case cons head tail iht =>
        simp_all
        obtain ⟨ih1, ih2⟩ := ih
        intro x hx
        have hh := ih1 x hx
        simp [LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic] at iht ⊢
        simp [he, hh]
        exact iht x hx''',
'''by
  by_cases he : S.hasEmptyScopes
  · simp_all [Subst.isEmpty_implies_keys_empty S he]
  · induction ty
    case ftvar i =>
      simp_all [LMonoTy.subst]
      intro id hid
      split
      · rename_i _ sty hs
        simp_all [SubstWF, Subst.freeVars]
        apply h id hid sty
        exact @Maps.find?_mem_values _ _ i sty _ S hs
      · simp_all [freeVars]
        have hn := @Maps.find?_of_not_mem_values _ _ i _ S
        simp_all
        exact ne_of_mem_of_not_mem hid hn
    case bitvec n => simp_all [LMonoTy.subst, LMonoTy.freeVars]
    case tcons name args ih =>
      simp_all
      simp [subst]
      induction args
      · simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic, LMonoTys.freeVars, LMonoTy.freeVars]
      · rename_i head tail iht
        simp_all
        obtain ⟨ih1, ih2⟩ := ih
        intro x hx
        have hh := ih1 x hx
        simp [LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic] at iht ⊢
        simp [he, hh]
        exact iht x hx''',
'''by
  by_cases he : S.hasEmptyScopes
  · simp_all [Subst.isEmpty_implies_keys_empty S he]
  · induction ty
    case ftvar i =>
      simp_all [LMonoTy.subst]
      intro id hid
      split
      · rename_i _ sty hs
        simp_all [SubstWF, Subst.freeVars]
        have hm := @Maps.find?_mem_values _ _ i sty _ S hs
        exact h id hid sty hm
      · simp_all [freeVars]
        have := @Maps.find?_of_not_mem_values _ _ i _ S
        simp_all
        exact ne_of_mem_of_not_mem hid this
    case bitvec n => simp_all [LMonoTy.subst, LMonoTy.freeVars]
    case tcons name args ih =>
      simp_all
      simp [subst]
      induction args <;> simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic, LMonoTys.freeVars, LMonoTy.freeVars]
      grind''',
],
'List.length_dedup_append_le_left': [
'''by
  have bound : ∀ {s t : List α}, s.Nodup → s ⊆ t → s.length ≤ t.length := by
    intro s
    induction s with
    | nil => simp
    | cons a as ih =>
      intro t hn hs
      have ha : a ∈ t := hs (by simp)
      obtain ⟨u, v, rfl⟩ := List.mem_iff_append.mp ha
      have ht : as ⊆ u ++ v := by grind
      have hl := ih (by simpa using hn.of_cons) ht
      simp at hl ⊢
      omega
  apply bound (nodup_dedup l₁)
  intro a ha
  exact mem_of_mem_dedup (l₁ ++ l₂) a (List.mem_append_left l₂ (mem_dedup_of_mem l₁ a ha))''',
'''by
  induction l₁ generalizing l₂
  case nil => simp [dedup]
  case cons a as ih =>
    simp [dedup]
    split
    · rename_i h
      have ha := (mem_of_dedup as a).mpr h
      have hb : a ∈ (as ++ l₂).dedup := mem_of_mem_dedup _ _ (by simp_all)
      simp_all
    · rename_i h
      by_cases ha : a ∈ (as ++ l₂).dedup
      · simp_all
        have hn : a ∉ as := by simpa [← mem_of_dedup] using h
        have hm := (mem_of_dedup (as ++ l₂) a).mpr ha
        rw [length_dedup_of_removeAll a (as ++ l₂) hm]
        have he : (as ++ l₂).removeAll [a] = as ++ l₂.removeAll [a] := by
          simp [removeAll]
          have hf : filter (fun x => !decide (x = a)) as = as := by
            simp_all
            intro x hx
            exact ne_of_mem_of_not_mem hx hn
          simp_all
        rw [he]
        exact Nat.sub_le_iff_le_add'.mp (ih (l₂.removeAll [a]))
      · simp_all''',
'''by
  have bound : ∀ (s t : List α), s.Nodup → s ⊆ t → s.length ≤ t.length := by
    intro s
    induction s with
    | nil => simp
    | cons x xs ih =>
      intro t hn hs
      have hx : x ∈ t := by apply hs; simp
      obtain ⟨u, v, rfl⟩ := List.mem_iff_append.mp hx
      have hsub : xs ⊆ u ++ v := by grind
      have hlen := ih (u ++ v) (List.nodup_cons.mp hn).2 hsub
      simp at hlen ⊢
      omega
  apply bound _ _ (nodup_dedup l₁)
  intro x hx
  apply mem_of_mem_dedup
  exact List.mem_append_left _ (mem_dedup_of_mem _ _ hx)''',
'''by
  have bound : ∀ {s t : List α}, s.Nodup → s ⊆ t → s.length ≤ t.length := by
    intro s
    induction s with
    | nil => simp
    | cons x xs ih =>
      intro t hn hs
      have hx : x ∈ t := hs (by simp)
      obtain ⟨u, v, rfl⟩ := List.mem_iff_append.mp hx
      have hsub : xs ⊆ u ++ v := by grind
      have hlen := ih (List.nodup_cons.mp hn).2 hsub
      simp only [List.length_cons, List.length_append] at *
      omega
  exact bound (nodup_dedup l₁) (fun x hx => mem_of_mem_dedup _ _ (List.mem_append_left _ (mem_dedup_of_mem _ _ hx)))''',
'''by
  have bound : ∀ {s t : List α}, s.Nodup → s ⊆ t → s.length ≤ t.length := by
    intro s
    induction s with
    | nil => simp
    | cons x xs ih =>
      intro t hn hs
      have hx : x ∈ t := hs (by simp)
      obtain ⟨u, v, rfl⟩ := List.mem_iff_append.mp hx
      have hsub : xs ⊆ u ++ v := by grind
      have hlen := ih (List.nodup_cons.mp hn).2 hsub
      grind
  apply bound (nodup_dedup l₁)
  intro x hx
  apply mem_of_mem_dedup
  have := mem_dedup_of_mem l₁ x hx
  simp_all''',
],
'Lambda.Factory.addFactory_wf': [
'''by
  unfold Factory.addFactory
  rw [← Array.foldlM_toList]
  generalize Hl : newF.toList = l
  induction l generalizing newF F
  · rw [Array.toList_eq_nil_iff] at Hl
    rw [List.foldlM_nil]
    unfold Pure.pure Except.instMonad Except.pure
    grind
  · rename_i lf tail ih
    have he : newF = [lf].toArray ++ tail.toArray := by grind
    have ht : FactoryWF tail.toArray := by
      rw [he] at newF_wf
      constructor
      · have hn := newF_wf.name_nodup; grind
      · intro f hf
        exact newF_wf.lfuncs_wf f (Array.mem_append_right _ hf)
    have hh : LFuncWF lf := by
      rw [he] at newF_wf
      apply newF_wf.lfuncs_wf
      apply Array.mem_append_left
      grind
    intro F'
    simp only [List.foldlM]
    unfold bind Except.instMonad Except.bind
    intro h
    split at h
    · contradiction
    · rename_i mid hm
      have hw : FactoryWF mid := by apply Factory.addFactoryFunc_wf F F_wf lf <;> assumption
      simp only [] at h
      apply ih mid hw tail.toArray <;> grind''',
'''by
  unfold Factory.addFactory
  rw [← Array.foldlM_toList]
  generalize Hl : newF.toList = l
  induction l generalizing newF F
  · rw [Array.toList_eq_nil_iff] at Hl
    simp only [List.foldlM_nil]
    unfold Pure.pure Except.instMonad Except.pure
    grind
  · rename_i lf tail ih
    have he : newF = [lf].toArray ++ tail.toArray := by grind
    have ht : FactoryWF tail.toArray := by
      rw [he] at newF_wf
      constructor
      · have hn := newF_wf.name_nodup; grind
      · intros f hf
        apply newF_wf.lfuncs_wf f
        apply Array.mem_append_right
        exact hf
    have hh : LFuncWF lf := by
      rw [he] at newF_wf
      apply newF_wf.lfuncs_wf
      apply Array.mem_append_left
      grind
    intro F'
    simp only [List.foldlM]
    unfold bind Except.instMonad
    simp only []
    unfold Except.bind
    intro h
    split at h
    · contradiction
    · rename_i mid hm
      have hw : FactoryWF mid := by apply Factory.addFactoryFunc_wf F F_wf lf <;> assumption
      simp only [] at h
      exact ih mid hw tail.toArray ht (by simp) F' h''',
'''by
  unfold Factory.addFactory
  rw [← Array.foldlM_toList]
  generalize Hl : newF.toList = l
  induction l generalizing newF F
  · rw [Array.toList_eq_nil_iff] at Hl
    rw [List.foldlM_nil]
    unfold Pure.pure Except.instMonad Except.pure
    grind
  · rename_i lf tail ih
    have he : newF = [lf].toArray ++ tail.toArray := by grind
    have ht : FactoryWF tail.toArray := by
      rw [he] at newF_wf
      constructor
      · have hn := newF_wf.name_nodup; grind
      · intro f hf
        apply newF_wf.lfuncs_wf f
        apply Array.mem_append_right
        assumption
    have hh : LFuncWF lf := by
      rw [he] at newF_wf
      apply newF_wf.lfuncs_wf
      apply Array.mem_append_left
      grind
    intro F'
    simp only [List.foldlM]
    unfold bind Except.instMonad
    simp only []
    unfold Except.bind
    intro h
    split at h
    · contradiction
    · rename_i mid hm
      have hw : FactoryWF mid := by apply Factory.addFactoryFunc_wf F F_wf lf <;> assumption
      simp only [] at h
      apply ih mid hw tail.toArray <;> grind''',
'''by
  unfold Factory.addFactory
  rw [← Array.foldlM_toList]
  generalize Hl : newF.toList = l
  induction l generalizing newF F
  · rw [Array.toList_eq_nil_iff] at Hl
    rw [List.foldlM_nil]
    unfold Pure.pure Except.instMonad Except.pure
    grind
  · rename_i lf tail ih
    have he : newF = [lf].toArray ++ tail.toArray := by grind
    have ht : FactoryWF tail.toArray := by
      rw [he] at newF_wf
      refine ⟨?_, ?_⟩
      · have hn := newF_wf.name_nodup; grind
      · intro f hf
        apply newF_wf.lfuncs_wf f
        exact Array.mem_append_right _ hf
    have hh : LFuncWF lf := by
      rw [he] at newF_wf
      apply newF_wf.lfuncs_wf
      exact Array.mem_append_left _ (by simp)
    intro F'
    simp only [List.foldlM]
    unfold bind Except.instMonad
    simp only []
    unfold Except.bind
    intro h
    split at h
    · contradiction
    · rename_i mid hm
      have hw : FactoryWF mid := by apply Factory.addFactoryFunc_wf F F_wf lf <;> assumption
      simp only [] at h
      apply ih mid hw tail.toArray <;> grind''',
'''by
  unfold Factory.addFactory
  rw [← Array.foldlM_toList]
  generalize Hl : newF.toList = l
  induction l generalizing newF F
  · rw [Array.toList_eq_nil_iff] at Hl
    simp [List.foldlM_nil]
    grind
  · rename_i lf tail ih
    have he : newF = [lf].toArray ++ tail.toArray := by grind
    have ht : FactoryWF tail.toArray := by
      rw [he] at newF_wf
      constructor
      · have hn := newF_wf.name_nodup; grind
      · intro f hf
        apply newF_wf.lfuncs_wf f
        apply Array.mem_append_right
        exact hf
    have hh : LFuncWF lf := by
      rw [he] at newF_wf
      apply newF_wf.lfuncs_wf
      apply Array.mem_append_left
      grind
    intro F'
    simp only [List.foldlM]
    unfold bind Except.instMonad
    simp only []
    unfold Except.bind
    intro h
    split at h
    · contradiction
    · rename_i mid hm
      have hw : FactoryWF mid := by apply Factory.addFactoryFunc_wf F F_wf lf <;> assumption
      simp only [] at h
      apply ih mid hw tail.toArray <;> grind''',
],
'Lambda.LMonoTy.freeVars_of_subst_subset': [
'''by
  by_cases he : S.hasEmptyScopes
  · unfold subst; simp_all [Subst.hasEmptyScopes]
  · simp [Subst.freeVars]
    induction mty
    case ftvar x =>
      simp_all [subst]
      split
      · rename_i sty hs
        intro v hv
        simp_all
        right
        exact ⟨sty, Maps.find?_mem_values hs, hv⟩
      · simp [freeVars]
    case bitvec n => simp [subst]
    case tcons name args ih =>
      simp [LMonoTy.subst, LMonoTy.freeVars]
      induction args
      · simp_all [LMonoTys.freeVars, LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
      · rename_i head tail iht
        simp at he
        simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
        simp [freeVars] at *
        grind''',
'''by
  by_cases he : S.hasEmptyScopes
  · unfold subst; simp_all [Subst.hasEmptyScopes]
  · simp [Subst.freeVars]
    induction mty
    case ftvar x =>
      simp_all [subst]
      split
      · rename_i sty hs
        intro v hv; simp_all; right
        apply Exists.intro sty
        simp [hv]
        exact @Maps.find?_mem_values _ _ x sty _ S hs
      · simp [freeVars]
    case bitvec n => simp [subst]
    case tcons name args ih =>
      simp [LMonoTy.subst, LMonoTy.freeVars]
      induction args
      · simp_all [LMonoTys.freeVars, LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
      · rename_i head tail iht
        simp at he
        simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
        simp [freeVars] at *
        grind''',
'''by
  by_cases he : S.hasEmptyScopes
  · unfold subst; simp_all [Subst.hasEmptyScopes]
  · simp [Subst.freeVars]
    induction mty
    case ftvar x =>
      simp_all [subst]
      split
      · rename_i sty hs
        intro v hv; simp_all; right
        apply Exists.intro sty
        simp [hv]
        exact @Maps.find?_mem_values _ _ x sty _ S hs
      · simp [freeVars]
    case bitvec n => simp [subst]
    case tcons name args ih =>
      simp [LMonoTy.subst, LMonoTy.freeVars]
      induction args
      case nil => simp_all [LMonoTys.freeVars, LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
      case cons mty mtys iht =>
        simp at he
        simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
        simp [freeVars] at *
        generalize (subst S mty).freeVars = x at iht ih
        generalize mty.freeVars = a at iht ih
        generalize LMonoTys.freeVars mtys = b at iht ih
        generalize List.flatMap freeVars (Maps.values S) = c at iht ih
        generalize (LMonoTys.substLogic S mtys).freeVars = d at iht ih
        obtain ⟨ih1, ih2⟩ := ih
        constructor
        · intro v hv
          have hm := ih1 hv
          simp only [List.mem_append] at hm ⊢
          tauto
        · exact List.subset_append_of_subset_right a iht''',
'''by
  by_cases he : S.hasEmptyScopes
  · unfold subst; simp_all [Subst.hasEmptyScopes]
  · simp [Subst.freeVars]
    induction mty
    case ftvar x =>
      simp_all [subst]
      split
      · rename_i sty hs
        intro v hv; simp_all; right
        apply Exists.intro sty
        simp [hv]
        exact @Maps.find?_mem_values _ _ x sty _ S hs
      · simp [freeVars]
    case bitvec n => simp [subst]
    case tcons name args ih =>
      simp [LMonoTy.subst, LMonoTy.freeVars]
      induction args
      case nil => simp_all [LMonoTys.freeVars, LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
      case cons mty mtys iht =>
        simp at he
        simp_all [LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
        simp [freeVars] at *
        generalize (subst S mty).freeVars = x at iht ih
        generalize mty.freeVars = a at iht ih
        generalize LMonoTys.freeVars mtys = b at iht ih
        generalize List.flatMap freeVars (Maps.values S) = c at iht ih
        generalize (LMonoTys.substLogic S mtys).freeVars = d at iht ih
        obtain ⟨ih1, ih2⟩ := ih
        constructor
        · intro v hv
          have hm := ih1 hv
          simp only [List.mem_append] at hm ⊢
          rcases hm with hm | hm
          · exact Or.inl hm
          · exact Or.inr (Or.inr hm)
        · exact List.subset_append_of_subset_right a iht''',
'''by
  by_cases he : S.hasEmptyScopes
  · unfold subst; simp_all [Subst.hasEmptyScopes]
  · simp [Subst.freeVars]
    induction mty
    case ftvar x =>
      simp_all [subst]
      split
      · rename_i sty hs
        intro v hv; simp_all; right
        apply Exists.intro sty
        simp [hv]
        exact @Maps.find?_mem_values _ _ x sty _ S hs
      · simp [freeVars]
    case bitvec n => simp [subst]
    case tcons name args ih =>
      simp [LMonoTy.subst, LMonoTy.freeVars]
      induction args <;> simp_all [LMonoTys.freeVars, LMonoTy.freeVars, LMonoTys.subst_eq_substLogic, LMonoTys.substLogic]
      grind''',
],
}
