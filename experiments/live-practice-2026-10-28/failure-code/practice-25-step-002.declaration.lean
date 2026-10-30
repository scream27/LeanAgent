theorem substOldExprPostSubset:
  (Imperative.HasVarsPure.getVars (P:=Expression)
    (substsOldExpr ((h2, (Lambda.LExpr.fvar m h1 ty))::t) post)).Subset
    (Imperative.HasVarsPure.getVars (P:=Expression) (substsOldExpr t post) ++ [h1]) := by
  induction post
  any_goals (simp only [Imperative.HasVarsPure.getVars, substsOldExpr, Map.isEmpty, Bool.false_eq_true, ↓reduceIte, ite_self] at *; try apply List.subset_append_left)
  any_goals (by_cases Hnil: t = [] <;> (simp only [Hnil]; simp only [Bool.false_eq_true, ↓reduceIte, Lambda.LExpr.LExpr.getVars]); try apply substOldExprPostSubset'; try assumption)
  any_goals (try simp only [Hnil, List.append_assoc] at *; try rw [OldExpressions.substOldExpr_nil] at *)
  any_goals (apply List.append_subset.mpr; constructor <;> try apply List.Subset.trans (by assumption); try apply List.append_subset.mpr; constructor)
  any_goals (apply List.append_subset.mpr; constructor)
  any_goals apply List.Subset.assoc.mp
  any_goals (solve | apply List.Subset.subset_app_of_or_3; simp)
  split <;> try split
  any_goals (split <;> try split)
  any_goals split
  any_goals (simp [Map.find?] at *)
  any_goals simp [Lambda.LExpr.LExpr.getVars]
  any_goals (apply substOldExprPostSubset'')
  any_goals apply List.Subset.trans (by assumption)
  any_goals (apply List.append_subset.mpr; constructor)
  any_goals (repeat apply List.Subset.assoc.mp)
  any_goals apply List.Subset.subset_app_of_or_4
  any_goals simp [Imperative.HasVarsPure.getVars]
  rename_i H; simp [← H.right, Lambda.LExpr.LExpr.getVars]
  constructor <;> (apply substOldExprPostSubset''; apply List.Subset.assoc.mp; apply List.append_subset.mpr; constructor <;> (apply List.Subset.subset_app_of_or_3; simp[Imperative.HasVarsPure.getVars]))
  rename_i H _ _ _
  split at H <;> try contradiction
  apply List.Subset.subset_app_of_or_2
  simp at H
  simp [← H, Lambda.LExpr.LExpr.getVars]
  simp_all
  apply List.Subset.subset_app_of_or_2; simp
  rename_i H _ _
  split at H <;> try contradiction
  simp at H
  simp [← H, Lambda.LExpr.LExpr.getVars, List.Subset]
  simp_all
  rename_i H _ _ _
  split at H <;> try contradiction
  simp_all
  unfold substsOldExpr; simp [Map.isEmpty, Lambda.LExpr.LExpr.getVars]
  apply List.Subset.trans (by assumption)
  any_goals (try apply List.Subset.trans (by assumption); apply List.append_subset.mpr <;> constructor)
  apply List.append_subset.mpr; constructor
  any_goals (try apply List.Subset.assoc.mp; apply List.Subset.subset_app_of_or_3; simp)
