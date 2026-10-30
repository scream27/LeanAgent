theorem updatedStatesDefMonotone
  {P : PureExpr} {σ : SemanticStore P}
  {vs : List P.Ident} {ves : List (P.Ident × P.Expr)} :
  isDefined σ vs →
  isDefined (updatedStates' σ ves) vs := by
  intros Hdef
  induction ves generalizing σ <;>
  unfold updatedStates' <;> try simp_all
  case cons h t ih =>
    simp [isDefined]
    intros v Hin
    apply ih
    exact updatedStateDefMonotone Hdef
    assumption

  theorem updatedStatesDefined :
  ks.length = vs.length →
  isDefined (updatedStates σ ks vs) ks := by
  intros Hlen k Hin
  induction ks generalizing σ vs <;> simp_all
  case cons h t ih =>
  simp [updatedStates] at *
  cases vs <;> simp at Hlen
  case cons h' t' =>
  cases Hin with
  | inl Hin =>
    simp [updatedStates']
    have Hdef : isDefined (updatedStates' (updatedState σ h h') (t.zip t')) [h] := by
      apply updatedStatesDefMonotone
      simp [isDefined, updatedState]
    simp_all [isDefined]
  | inr Hin =>
    apply ih <;> assumption