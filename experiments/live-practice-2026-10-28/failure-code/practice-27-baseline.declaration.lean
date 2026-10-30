theorem InitUpdateComm
  {P : PureExpr} {σ σ' σ'' : SemanticStore P}
  {k k' : P.Ident} {v v' : P.Expr}
  :
  UpdateState P σ k v σ' →
  InitState P σ' k' v' σ'' →
  ∃ σ₁,
    σ₁ = (updatedState σ k' v') ∧
    InitState P σ k' v' σ₁ ∧
    UpdateState P σ₁ k v σ'' := by
  intros Hup Hinit
  exists (updatedState σ k' v')
  have Hk : (isDefined σ' [k]) := UpdateStateDefined Hup
  have Hups : UpdateStates σ [k] [v] σ' := by
    apply UpdateStates.update_some Hup UpdateStates.update_none
  have Hinits : InitStates σ' [k'] [v'] σ'' := by
    apply InitStates.init_some Hinit InitStates.init_none
  have Hcomms := InitsUpdatesComm Hups Hinits
  simp at Hcomms
  refine ⟨rfl, ?_, ?_⟩
  . have Hinit := Hcomms.1
    cases Hinit with
    | init_some Hinit Hinits =>
    simp [InitStatesEmpty Hinits, updatedStates, updatedStates'] at Hinit
    assumption
  . have Hup := Hcomms.2
    cases Hup with
    | update_some Hup Hups =>
    simp [UpdateStatesEmpty Hups, updatedStates, updatedStates'] at Hup
    assumption