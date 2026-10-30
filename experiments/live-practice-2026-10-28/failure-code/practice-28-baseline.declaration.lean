theorem InitStatesSubstStores :
ReadValues σ ks' vs' →
InitStates σ ks vs' σ' →
substStores σ σ' (ks'.zip ks) := by
intros Hrd Hinit
induction Hinit generalizing ks' with
| init_none =>
  simp [substStores]
| init_some Hinit Hinits ih =>
  next σ x v σ₁ xs vs σ'' =>
  cases Hrd with
  | read_some Hsome'' Hrds =>
  next ys y =>
  have Hinit' := Hinit
  cases Hinit with
  | init Hnone Hsome' Heq =>
  simp [substStores]
  intros k1 k2 Hin
  cases Hin with
  | inl Hin =>
    simp_all
    apply Eq.symm
    apply InitStatesSomeMonotone Hsome' Hinits
  | inr Hin =>
    specialize @ih ys ?_
    exact InitStateReadValuesMonotone Hrds Hinit'
    rw [← Heq]
    exact ih k1 k2 Hin
    apply Not.intro
    intro Heq
    simp_all
    have Hin' := List.of_mem_zip Hin
    have Hdef := ReadValuesIsDefined Hrds
    specialize Hdef k1 Hin'.1
    simp_all