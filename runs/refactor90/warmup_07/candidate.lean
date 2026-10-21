lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have h := der.wf
  induction der <;> subst eq <;>
    grind only [→ wf, → canonical_form_abs, → canonical_form_tabs, → canonical_form_sum,
      → Red.appₗ, → Red.appᵣ, → Red.tapp, → Red.abs, → Red.tabs, → Red.let_bind, → Red.let_body, → Red.inl, → Red.inr, → Red.case, → Red.case_inl, → Red.case_inr, → Value.abs, → Value.tabs, → Value.inl, → Value.inr, cases Term.LC, cases Value, = body_let, = body_case,
      cases Ty.Wf, Option.mem_def, dlookup_nil]
