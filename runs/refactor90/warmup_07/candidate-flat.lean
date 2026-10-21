lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have lc := der.wf.2.1
  induction der <;> subst eq
  case' var mem => simp at mem
  case' app t₁ _ _ t₂ l r il ir =>
    rcases il rfl l.wf.2.1 with vl | ⟨t', hl⟩
  case' app.inl => rcases ir rfl r.wf.2.1 with vr | ⟨t', hr⟩
  case' app.inl.inl => obtain ⟨_, _, rfl⟩ := l.canonical_form_abs vl
  case' tapp σ' der sub ih =>
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
  case' tapp.inl => obtain ⟨_, _, rfl⟩ := der.canonical_form_tabs v
  case' let' t₁ σ t₂ τ L der _ ih _ =>
    have hb := (body_let.mp lc).2
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
  case' inl der _ ih => rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
  case' inr der _ ih => rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
  case' case t₁ _ _ t₂ _ t₃ _ der _ _ ih _ _ =>
    have hb := body_case.mp lc
    rcases ih rfl der.wf.2.1 with v | ⟨t', h⟩
  case' case.inl => obtain ⟨t', e | e⟩ := der.canonical_form_sum v <;> subst e
  case' sub der _ ih => exact ih rfl lc
  all_goals aesop (add safe forward [wf, Sub.wf, Wf.lc, Value.lc], safe cases Value,
    unsafe 50% constructors [Value, Red])
