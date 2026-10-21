lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  have der' : Typing Γ t τ := der
  induction der <;> subst eq
  case var mem => grind only [Option.mem_def, dlookup_nil]
  case app t₁ _ _ t₂ l r ih_l ih_r =>
    right
    cases ih_l rfl l with
    | inl val_l =>
        cases ih_r rfl r with
        | inl val_r =>
            have ⟨σ, t₁, eq⟩ := l.canonical_form_abs val_l
            exists t₁ ^ᵗᵗ t₂
            grind only [→ wf, Red.abs]
        | inr red_r =>
            obtain ⟨t₂', _⟩ := red_r
            exists t₁.app t₂'
            grind only [Red.appᵣ]
    | inr red_l =>
        obtain ⟨t₁', _⟩ := red_l
        exists t₁'.app t₂
        grind only [→ wf, Red.appₗ]
  case tapp σ' der _ ih =>
    right
    specialize ih rfl der
    cases ih with
    | inl val =>
        obtain ⟨_, t, _⟩ := der.canonical_form_tabs val
        exists t ^ᵗᵞ σ'
        grind only [→ wf, → Sub.wf, Red.tabs, → Wf.lc]
    | inr red =>
        obtain ⟨t', _⟩ := red
        exists .tapp t' σ'
        grind only [→ Sub.wf, Red.tapp, → Wf.lc]
  case let' t₁ σ t₂ τ L der _ ih _ =>
    right
    cases ih rfl der with
    | inl _ =>
        exists t₂ ^ᵗᵗ t₁
        grind only [→ wf, Red.let_body, body_let]
    | inr red =>
        obtain ⟨t₁', _⟩ := red
        exists t₁'.let' t₂
        grind only [→ wf, Red.let_bind, body_let]
  case inl der _ ih =>
    cases (ih rfl der) with
    | inl val => grind only [Value.inl]
    | inr red =>
        right
        obtain ⟨t', _⟩ := red
        exists .inl t'
        grind only [Red.inl]
  case inr der _ ih =>
    cases (ih rfl der) with
    | inl val => grind only [Value.inr]
    | inr red =>
        right
        obtain ⟨t', _⟩ := red
        exists .inr t'
        grind only [Red.inr]
  case case t₁ _ _ t₂ _ t₃ _ der _ _ ih _ _ =>
    right
    cases ih rfl der with
    | inl val =>
        have ⟨t₁, lr⟩ := der.canonical_form_sum val
        cases lr <;> [exists t₂ ^ᵗᵗ t₁; exists t₃ ^ᵗᵗ t₁] <;> grind only [→ wf, Red.case_inl, Red.case_inr, body_case]
    | inr red =>
        obtain ⟨t₁', _⟩ := red
        exists t₁'.case t₂ t₃
        grind only [→ wf, Red.case, body_case]
  case sub => grind only
  case abs σ _ τ L _ _=>
    left
    constructor
    apply LC.abs L
    · grind only [→ wf, cases Term.LC]
    · grind only [→ wf]
  case tabs L _ _=>
    left
    constructor
    apply LC.tabs L
    · grind only [→ wf, cases Term.LC]
    · grind only [→ wf]
