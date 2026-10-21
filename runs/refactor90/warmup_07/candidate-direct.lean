lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have lc := der.wf.2.1
  induction der <;> subst eq
  case var mem => simp at mem
  case abs => exact .inl (.abs lc)
  case tabs => exact .inl (.tabs lc)
  case app t₁ _ _ t₂ l r il ir =>
    rcases il rfl l.wf.2.1 with vl | ⟨t', hl⟩
    · rcases ir rfl r.wf.2.1 with vr | ⟨t', hr⟩
      · obtain ⟨_, _, rfl⟩ := l.canonical_form_abs vl
        exact .inr ⟨_, .abs vl.lc vr⟩
      · exact .inr ⟨_, .appᵣ vl hr⟩
    · exact .inr ⟨_, .appₗ r.wf.2.1 hl⟩
  case tapp σ' der sub ih =>
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
    · obtain ⟨_, _, rfl⟩ := der.canonical_form_tabs v
      exact .inr ⟨_, .tabs v.lc sub.wf.2.1.lc⟩
    · exact .inr ⟨_, .tapp sub.wf.2.1.lc h⟩
  case let' t₁ σ t₂ τ L der _ ih _ =>
    have hb := (body_let.mp lc).2
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
    · exact .inr ⟨_, .let_body v hb⟩
    · exact .inr ⟨_, .let_bind h hb⟩
  case inl der _ ih =>
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
    · exact .inl (.inl v)
    · exact .inr ⟨_, .inl h⟩
  case inr der _ ih =>
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
    · exact .inl (.inr v)
    · exact .inr ⟨_, .inr h⟩
  case case t₁ _ _ t₂ _ t₃ _ der _ _ ih _ _ =>
    have hb := body_case.mp lc
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
    · obtain ⟨t', e | e⟩ := der.canonical_form_sum v
      · subst e
        cases v with | inl v => exact .inr ⟨_, .case_inl v hb.2.1 hb.2.2⟩
      · subst e
        cases v with | inr v => exact .inr ⟨_, .case_inr v hb.2.1 hb.2.2⟩
    · exact .inr ⟨_, .case h hb.2.1 hb.2.2⟩
  case sub der _ ih => exact ih rfl lc
