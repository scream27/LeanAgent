lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have h := der.wf
  induction der <;> subst eq <;>
    aesop (add safe forward [wf, canonical_form_abs, canonical_form_tabs, canonical_form_sum],
      unsafe 50% constructors [Red, Value])
