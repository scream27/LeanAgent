open OldExpressions in
theorem substOldPostSubset:
  (Imperative.HasVarsPure.getVars (P:=Expression)
    (substOld h2 (Lambda.LExpr.fvar m h1 ty) post)).Subset
    (Imperative.HasVarsPure.getVars (P:=Expression) post ++ [h1]) := by
  induction post <;> unfold substOld <;> (try split <;> try split) <;>
    simp_all [Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] <;>
    (repeat' apply List.Subset.app) <;> (try (apply List.Subset.trans; assumption)) <;>
    simp +contextual [List.Subset, or_imp]
