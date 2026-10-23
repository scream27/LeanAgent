theorem InitsUpdatesComm
  {P : PureExpr} {σ σ' σ'' : SemanticStore P}
  {ks ks' : List P.Ident} {vs vs' : List P.Expr} :
  UpdateStates σ ks vs σ' →
  InitStates σ' ks' vs' σ'' →
  ∃ σ₁,
    σ₁ = (updatedStates σ ks' vs') ∧
    InitStates σ ks' vs' σ₁ ∧
    UpdateStates σ₁ ks vs σ'' := by
  intro h g
  have f := UpdateStatesNotDefMonotone' (InitStatesNotDefined g) h
  refine ⟨_, rfl, updatedStatesInit (InitStatesLength g) f (InitStatesNodup g), ?_⟩
  rw [InitStatesUpdated g, UpdateStatesUpdated h]
  unfold updatedStates
  rw [updatedStatesComm]
  · exact updatedStatesUpdate (UpdateStatesLength h)
      (updatedStatesDefMonotone (UpdateStatesDefined' h))
  · rw [List.unzip_zip (UpdateStatesLength h), List.unzip_zip (InitStatesLength g)]
    intro x a b
    simpa [f x b] using UpdateStatesDefined' h x a
