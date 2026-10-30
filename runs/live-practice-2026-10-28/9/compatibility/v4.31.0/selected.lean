/-- P ~ Q → P | R ~ Q | R -/
theorem bisimilarity_congr_par :
    (p ~[lts (defs := defs)] q) → (par p r) ~[lts (defs := defs)] (par q r) := by
  intro h
  exists @ParBisim _ _ defs
  constructor
  · grind
  intro s1 s2 r μ
  constructor
  case left =>
    intro s1' htr
    cases r
    unfold lts at *
    have : {Tr :=  Tr (defs := defs)} = lts (defs := defs) := by rfl
    case par p q r hbisim =>
      obtain ⟨rel, hr, hb⟩ := hbisim
      cases htr
      case parL p' htr =>
        obtain ⟨q', _⟩ := hb.follow_fst hr htr
        exists par q' r
        grind
      case parR r' htr =>
        exists par q r'
        grind
      case com r' _ htrp _ =>
        obtain ⟨q', _⟩ := hb.follow_fst hr htrp
        exists par q' r'
        grind
  case right =>
    intro s2' htr
    cases r
    unfold lts at *
    have : {Tr :=  Tr (defs := defs)} = lts (defs := defs) := by rfl
    case par p _ r hbisim =>
      obtain ⟨_, hr, hb⟩ := hbisim
      cases htr
      case parL htr =>
        obtain ⟨p', _⟩ := hb.follow_snd hr htr
        exists par p' r
        grind
      case parR _ _ r' htr =>
        exists par p r'
        grind
      case com r' hco htrq htrr =>
        obtain ⟨q', _⟩ := hb.follow_snd hr htrq
        exists par q' r'
        grind