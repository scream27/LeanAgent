theorem Lambda.LExpr.substFvarsCorrectZero :
  Core.WellFormedCoreEvalCong δ →
  Imperative.WellFormedSemanticEvalVar δ →
  Imperative.WellFormedSemanticEvalVal δ →
  Imperative.invStores σ σ' (Imperative.HasVarsPure.getVars e) →
  δ σ e = δ σ' e := by
  intros Hwfc Hwfvr Hwfvl Hinv
  induction e <;> simp at *
  case const c | op o ty | bvar x =>
    rw [Hwfvl.2, Hwfvl.2]
    constructor
    constructor
  case fvar m name ty =>
    simp [Imperative.WellFormedSemanticEvalVar] at Hwfvr
    specialize Hwfvr (Lambda.LExpr.fvar m name ty) name
    rw [Hwfvr, Hwfvr, Hinv]
    simp [Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars]
    simp [Imperative.HasFvar.getFvar]
    simp [Imperative.HasFvar.getFvar]
  case abs m ty e ih  =>
    specialize ih Hinv
    have Hwfc := Hwfc.abscongr σ σ' e e ih
    apply Hwfc
  case quant m k ty tr e trih eih =>
    simp [Imperative.invStores, Imperative.substStores,
          Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] at *
    simp [List.zip_append] at *
    specialize trih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      left; assumption
    specialize eih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      right; assumption
    apply Hwfc.quantcongr <;> assumption
  case app m fn e fih eih =>
    simp [Imperative.invStores, Imperative.substStores,
          Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] at *
    simp [List.zip_append] at *
    specialize fih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      left; assumption
    specialize eih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      right; assumption
    apply Hwfc.appcongr <;> assumption
  case ite m c t e cih tih eih =>
    simp [Imperative.invStores, Imperative.substStores,
          Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] at *
    simp [List.zip_append] at *
    specialize cih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      left; assumption
    specialize tih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      right; left; assumption
    specialize eih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      right; right; assumption
    apply Hwfc.itecongr <;> assumption
  case eq m e1 e2 e1ih e2ih =>
    simp [Imperative.invStores, Imperative.substStores,
          Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] at *
    simp [List.zip_append] at *
    specialize e1ih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      left; assumption
    specialize e2ih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      right; assumption
    apply Hwfc.eqcongr <;> assumption
