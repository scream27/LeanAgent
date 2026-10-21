lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have h := der.wf.2.1
  induction der <;> subst eq <;>
    aesop (add safe forward [wf, Sub.wf, Wf.lc, canonical_form_abs, canonical_form_tabs, canonical_form_sum],
      norm simp [body_let, body_case], safe forward Value.lc, safe cases Value, safe constructors Value, unsafe 50% constructors Red)
