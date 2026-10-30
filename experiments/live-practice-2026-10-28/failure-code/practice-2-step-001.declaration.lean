/-- We can't use arbitrary expressions for substitution,
    because then we can't say anything about the stores
    due to not knowing the exact form of the expressions -/
theorem Lambda.LExpr.substFvarCorrect :
  Core.WellFormedCoreEvalCong δ →
  Imperative.WellFormedSemanticEvalVar (P:=Expression) δ →
  Imperative.WellFormedSemanticEvalVal (P:=Expression) δ →
  Imperative.substStores σ σ' [(fro, to)] →
  -- NOTE: `to` shouldn't be referred to in the original expression as well, but it is not needed in this lemma.
  Imperative.invStores σ σ'
    ((@Imperative.HasVarsPure.getVars Expression _ _ e).removeAll [fro]) →
  -- NOTE: the old store is irrelevant because we assume congruence on old expressions as well,
  -- More relation between the old store would be needed if we remove old expression congruence from WellFormedSemanticEvalVal
  δ σ e = δ σ' (e.substFvar fro (createFvar to)) := by
  intros Hwfc Hwfvr Hwfvl Hsubst2 Hinv
  induction e <;> simp [Lambda.LExpr.substFvar, createFvar] at *
  case const c | op o ty | bvar x =>
    rw [Hwfvl.2]
    rw [Hwfvl.2]
    constructor
    constructor
  case fvar name ty =>
    simp [Imperative.WellFormedSemanticEvalVar] at Hwfvr
    split <;> try simp_all
    . simp [Imperative.substStores] at Hsubst2
      rw [Hwfvr]
      rw [Hwfvr]
      exact Hsubst2
      simp [Imperative.HasFvar.getFvar]
      simp [Imperative.HasFvar.getFvar]
    . next Hne =>
      simp [Imperative.invStores, Imperative.substStores,
            Imperative.HasVarsPure.getVars,
            Lambda.LExpr.LExpr.getVars, List.removeAll, Hne] at Hinv
      rw [Hwfvr]
      rw [Hwfvr]
      exact Hinv
      simp [Imperative.HasFvar.getFvar]
      simp [Imperative.HasFvar.getFvar]
  case abs m ty e ih  =>
    exact Hwfc.1 σ σ' _ _ (ih Hinv)
  case quant m k ty tr e trih eih =>
    simp [Imperative.invStores, Imperative.substStores,
          Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] at *
    simp [List.app_removeAll, List.zip_append] at *
    specialize eih ?_
    · intros k1 k2 Hin
      rw [Hinv]
      right;
      assumption
    specialize trih ?_
    · intros k1 k2 Hin
      rw [Hinv]
      left;
      assumption
    apply Hwfc.quantcongr <;> assumption
  case app m c fn fih eih =>
    simp [Imperative.invStores, Imperative.substStores,
          Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] at *
    simp [List.app_removeAll, List.zip_append] at *
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
    simp [List.app_removeAll, List.zip_append] at *
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
    simp [List.app_removeAll, List.zip_append] at *
    specialize e1ih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      left; assumption
    specialize e2ih ?_
    . intros k1 k2 Hin
      rw [Hinv]
      right; assumption
    apply Hwfc.eqcongr <;> assumption
