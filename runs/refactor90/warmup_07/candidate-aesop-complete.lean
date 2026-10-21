lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have h := der.wf
  induction der <;> subst eq <;>
    aesop (add safe forward [wf, Sub.wf, Wf.lc, canonical_form_abs, canonical_form_tabs, canonical_form_sum],
      norm simp [body_let, body_case], safe cases Value, unsafe 50% constructors [Red, Value])
