theorem substOld_create_replace :
NormalizedOldExpr e →
(extractOldExprVars (substOld h (createFvar h') e)) =
(extractOldExprVars e).removeAll [h] := by
  intros Hnorm
  induction Hnorm <;> simp [extractOldExprVars, createFvar, substOld] at * <;> try assumption
  case app fn e m Hnfn Hne Hwf ih1 ih2 =>
    split
    . -- is old var
      next e1 e2 ty x ty =>
      split <;> simp [extractOldExprVars, List.removeAll] <;> simp_all
    . -- is a normal expression (non-old)
      next e1 e2 HH =>
      have Hnold : ¬ IsOldPred fn := by
        intros Hold
        specialize Hwf Hold
        cases Hold
        cases Hwf
        simp_all
        simp [CoreIdent.unres] at HH
        rename_i md tyy id v
        have HH2 := HH md tyy () id v
        simp_all
      have Hnold' : ¬ IsOldPred (substOld h (Lambda.LExpr.fvar () h' none) fn) := by
        intro Hold
        exact Hnold (substOldIsOldPred' (by intro H; cases H) Hold)
      unfold extractOldExprVars
      simp
      split <;> simp_all
      . -- old var, contradiction
        exfalso; apply Hnold'; constructor
      . -- old expr, contradiction
        exfalso; apply Hnold'; constructor
      split
      · rename_i x1 x2 x3 m1 id ty2 x7
        exact (HH x2 x3 m1 id ty2 rfl rfl).elim
      . -- old expr, contradiction
        exfalso; apply Hnold; constructor
      . simp [List.app_removeAll]
  case ite c t e cih tih eih =>
    simp [cih, tih, eih, List.app_removeAll]
  case eq e1 e2 e1ih e2ih =>
    simp [e1ih, e2ih, List.app_removeAll]
  case quant tr e trih eih =>
    simp [trih, eih, List.app_removeAll]
