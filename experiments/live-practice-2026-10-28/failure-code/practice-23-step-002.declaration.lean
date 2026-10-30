theorem substOldExpr_cons:
  Imperative.substNodup (createOldStoreSubst (h::t)) →
  OldExpressions.substsOldExpr (createOldVarsSubst (h :: t)) e
          = OldExpressions.substsOldExpr (createOldVarsSubst t) (OldExpressions.substOld h.snd (createFvar h.1.fst) e) := by
  intro Hnd
  induction e
  case app Hfn He =>
    simp [OldExpressions.substsOldExpr, createOldVarsSubst, Map.isEmpty, OldExpressions.substOld, createFvar]
    split; split; split
    simp [OldExpressions.substOld, createFvar,Map.find? , *, createOldVarsSubst.go] at *
    rename_i H; simp [← H, OldExpressions.substsOldExpr]
    simp_all [OldExpressions.substOld, createFvar,Map.find?, createOldVarsSubst.go]
    rename_i H _; split at H <;> simp_all [OldExpressions.substsOldExpr]
    intro; simp_all [Map.isEmpty]; rename_i H; split at H <;> simp_all [Map.find?]
    split <;> (rename_i H _; simp [*, createOldVarsSubst.go, Map.find?] at H)
    split at H; contradiction
    unfold OldExpressions.substsOldExpr
    split <;> simp [*]
    simp_all [createOldVarsSubst, createFvar]
    rename_i _ fn e _ _ H
    generalize H1: (OldExpressions.substOld h.snd (Lambda.LExpr.fvar () h.fst.fst none) fn) = fn'
    generalize H2: (OldExpressions.substOld h.snd (Lambda.LExpr.fvar () h.fst.fst none) e) = e'
    rw (occs := [3]) [Core.OldExpressions.substsOldExpr.eq_def]
    simp; split
    simp_all [Map.isEmpty]; rename_i H; split at H <;> simp_all
    rw[OldExpressions.substOldExpr_nil, OldExpressions.substOldExpr_nil]; simp
    split; split
    unfold OldExpressions.substOld at H1
    split at H1 <;> simp_all
    unfold OldExpressions.substOld at H2
    split at H2 <;> simp_all; grind
    split at H2; split at H2
    any_goals simp_all
    simp [← H2.left] at *
    have : Map.find? (List.map createOldVarsSubst.go t) h.fst.fst = none :=by
      simp [Imperative.substNodup, createOldStoreSubst, createOldStoreSubst.go] at Hnd
      have Hnd := Hnd.right
      have : List.map (Prod.fst ∘ createOldStoreSubst.go) t = List.map (Prod.fst ∘ createOldVarsSubst.go) t := by
        simp [createOldStoreSubst.go, createOldVarsSubst.go]
      have : ¬ h.fst.fst ∈ List.map (Prod.fst ∘ createOldVarsSubst.go) t := by
       rw[← this]
       rw [List.nodup_append] at Hnd
       false_or_by_contra
       have Hnd := Hnd.right.right h.fst.fst (by assumption) h.fst.fst (by simp)
       contradiction
      apply Map.findNone_eq_notmem_mapfst.mp
      simp only [List.map_map]
      assumption
    simp_all
    split at H1 <;> try simp_all
    split at H1 <;> try simp_all
    simp [OldExpressions.substsOldExpr]
  any_goals simp [OldExpressions.substsOldExpr, OldExpressions.substOld, createOldVarsSubst, Map.isEmpty]
  any_goals (split <;> rename_i H; split at H)
  any_goals (simp_all [createOldVarsSubst];  rw [OldExpressions.substOldExpr_nil])
  any_goals simp_all
  any_goals (split at H <;> try contradiction)
  any_goals simp_all [createOldVarsSubst]
  any_goals rw [OldExpressions.substOldExpr_nil]
  simp [createFvar, OldExpressions.substOldExpr_nil]
