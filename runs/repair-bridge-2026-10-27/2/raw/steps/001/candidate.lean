open OldExpressions in
theorem extractedOldExprInVars :
  NormalizedOldExpr post →
  (extractOldExprVars post).Subset
  (Imperative.HasVarsPure.getVars post) := by
  intro h
  induction h <;> simp_all [extractOldExprVars, Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars, List.Subset]
