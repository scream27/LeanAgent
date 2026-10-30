theorem substOldCorrect :
  Imperative.WellFormedSemanticEvalVar δ →
  Imperative.WellFormedSemanticEvalVal δ →
  Core.WellFormedCoreEvalCong δ →
  Core.WellFormedCoreEvalTwoState δ σ₀ σ →
  OldExpressions.NormalizedOldExpr e →
  --Imperative.invStores σ₀ σ
  --  ((OldExpressions.extractOldExprVars e).removeAll [fro]) →
  Imperative.substDefined σ₀ σ [(fro, to)] →
  Imperative.substStores σ₀ σ [(fro, to)] →
  -- substitute the store and the expression simultaneously
  δ σ e = δ σ (OldExpressions.substOld fro (createFvar to) e) := by
  intros Hwfvr Hwfvl Hwfc Hwf2 Hnorm Hdef Hsubst
  induction e <;> simp [OldExpressions.substOld] at *
  case abs m ty e ih  =>
    cases Hnorm with
    | abs Hnorm =>
      apply Hwfc.1
      apply ih Hnorm
  case quant m k ty tr e trih eih =>
    cases Hnorm with
    | quant Ht He =>
      specialize eih He
      specialize trih Ht
      apply Hwfc.quantcongr <;> grind
  case app m c fn fih eih =>
    cases Hnorm with
    | app Hc Hfn Hwf =>
    specialize fih Hc
    specialize eih Hfn
    split
    . -- is an old var
      split
      . -- is an old var that is substituted
        next x ty eq =>
        simp [eq] at *
        simp [WellFormedCoreEvalTwoState] at Hwf2
        rcases Hwf2.1 with ⟨vs, vs', σ₁, Hwf2'⟩
        by_cases Hin : fro ∈ vs
        case pos =>
        -- old var is modified
          have HH:= Hwf2.2.1 vs vs' σ₀ σ₁ σ Hwf2'.1 Hwf2'.2 fro
          simp [OldExpressions.oldVar,
                OldExpressions.oldExpr,
                CoreIdent.unres, Hin] at HH
          rw [HH]
          simp [createFvar]
          simp [Imperative.WellFormedSemanticEvalVar] at Hwfvr
          rw [Hwfvr (v:=to)]
          apply Hsubst
          exact List.mem_singleton.mpr rfl
          simp [Imperative.HasFvar.getFvar]
        case neg =>
        -- old var is not modified
          obtain ⟨as, Hup⟩ := HavocVarsUpdateStates Hwf2'.1
          obtain ⟨bs, Hinit⟩ := InitVarsInitStates Hwf2'.2
          have Hsubst' := substStoresUpdatesInv' ?_ Hsubst Hup
          have Hsubst'' := substStoresInitsInv' ?_ Hsubst' Hinit
          . have HH:= Hwf2.2.1 vs vs' σ₀ σ₁ σ Hwf2'.1 Hwf2'.2 fro
            simp [OldExpressions.oldVar,
                  OldExpressions.oldExpr,
                  CoreIdent.unres, Hin] at HH
            simp [createFvar]
            simp [HH]
            simp [Imperative.WellFormedSemanticEvalVar] at Hwfvr
            rw [Hwfvr (v:=to)]
            . simp [Imperative.substStores] at Hsubst''
              exact Hsubst''
            . simp [Imperative.HasFvar.getFvar]
          . simp [Imperative.substDefined] at *
            have Hdef' : Imperative.isDefined σ₀ [fro] := by
              simp [Imperative.isDefined]
              exact Hdef.1
            have Hdef'' := UpdateStatesDefMonotone Hdef' Hup
            simp [Imperative.isDefined] at Hdef''
            refine ⟨Hdef'', Hdef.2⟩
          . simp [List.Disjoint]
            intros a Hin Heq
            simp [Heq] at *
            contradiction
      . -- is an old var that is not substituted, use congruence
        rename_i e1 e2 mOp ty0 mVar x ty1 h
        simp at m mOp ty0 mVar x ty1
        apply Hwfc.appcongr <;> grind
    . -- is not an old var, use congruence
      apply Hwfc.appcongr <;> grind
  case ite m c t e cih tih eih =>
    cases Hnorm with
    | ite Hc Ht He =>
      specialize cih Hc
      specialize tih Ht
      specialize eih He
      apply Hwfc.itecongr <;> grind
  case eq m e1 e2 e1ih e2ih =>
    cases Hnorm with
    | eq He1 He2 =>
    specialize e2ih He2
    apply Hwfc.eqcongr <;> grind
