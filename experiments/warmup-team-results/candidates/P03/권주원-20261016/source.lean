by
  intro hup hi
  have lu := UpdateStatesLength hup
  have li := InitStatesLength hi
  refine ⟨_, rfl, updatedStatesInit li (UpdateStatesNotDefMonotone' (InitStatesNotDefined hi) hup) (InitStatesNodup hi), ?_⟩
  cases InitStatesUpdated hi
  cases UpdateStatesUpdated hup
  unfold updatedStates
  rw [updatedStatesComm]
  · apply updatedStatesUpdate lu
    apply updatedStatesDefMonotone
    exact UpdateStatesDefined' hup
  · simp_all only [List.unzip_zip]
    intro k hk hk'
    simpa [InitStatesNotDefined hi k hk'] using UpdateStatesDefined hup k hk
