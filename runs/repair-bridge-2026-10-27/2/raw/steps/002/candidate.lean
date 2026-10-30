open OldExpressions in
theorem extractedOldExprInVars :
  NormalizedOldExpr post →
  (extractOldExprVars post).Subset
  (Imperative.HasVarsPure.getVars post) := by
  intro h
  induction h <;> unfold extractOldExprVars <;> (try split) <;>
    simp_all [Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] <;>
    (repeat' apply List.Subset.app) <;> (try (apply List.Subset.trans; assumption)) <;>
    simp +contextual [List.Subset]
