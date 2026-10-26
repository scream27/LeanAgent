lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  -- Retain the typing derivation to recover local closure after induction.
  have wholeTyped : Typing Γ t τ := der
  induction der <;> subst eq
  case var => grind
  case app t₁ _ _ t₂ leftTyped rightTyped ihLeft ihRight =>
    right
    rcases ihLeft rfl leftTyped with leftValue | ⟨t₁', step⟩
    · rcases ihRight rfl rightTyped with rightValue | ⟨t₂', step⟩
      · obtain ⟨σ, body, rfl⟩ := leftTyped.canonical_form_abs leftValue
        exact ⟨_, Red.abs leftValue.lc rightValue⟩
      · exact ⟨_, Red.appᵣ leftValue step⟩
    · exact ⟨_, Red.appₗ rightTyped.wf.2.1 step⟩
  case tapp σ' typed _ ih =>
    right
    rcases ih rfl typed with value | ⟨t', step⟩
    · obtain ⟨_, body, eq⟩ := typed.canonical_form_tabs value
      refine ⟨body ^ᵗᵞ σ', ?_⟩
      grind
    · refine ⟨.tapp t' σ', ?_⟩
      grind
  case let' t₁ σ t₂ τ L typed _ ih _ =>
    right
    rcases ih rfl typed with value | ⟨t₁', step⟩
    · refine ⟨t₂ ^ᵗᵗ t₁, ?_⟩
      grind
    · refine ⟨t₁'.let' t₂, ?_⟩
      grind
  case inl typed _ ih | inr typed _ ih =>
    -- The two injections share the same value and congruence-step argument.
    rcases ih rfl typed with value | ⟨t', step⟩
    · left
      constructor
      exact value
    · right
      exact ⟨_, by constructor; exact step⟩
  case case t₁ _ _ t₂ _ t₃ _ typed _ _ ih _ _ =>
    right
    rcases ih rfl typed with value | ⟨t₁', step⟩
    · obtain ⟨t₁, side⟩ := typed.canonical_form_sum value
      have bodies := Term.body_case.mp wholeTyped.wf.2.1
      rcases side with rfl | rfl
      · cases value with
        | inl val => exact ⟨_, Red.case_inl val bodies.2.1 bodies.2.2⟩
      · cases value with
        | inr val => exact ⟨_, Red.case_inr val bodies.2.1 bodies.2.2⟩
    · refine ⟨t₁'.case t₂ t₃, ?_⟩
      grind
  case sub => grind
  case abs | tabs =>
    left
    constructor
    exact wholeTyped.wf.2.1
