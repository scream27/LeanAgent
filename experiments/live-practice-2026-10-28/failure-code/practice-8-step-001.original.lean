/-- P | (Q | R) ~ (P | Q) | R -/
theorem bisimilarity_par_assoc :
    (par p (par q r)) ~[lts (defs := defs)] (par (par p q) r) := by
  use ParAssoc, ParAssoc.assoc
  intro s1 s2 hr μ
  apply And.intro <;> cases hr
  case right.assoc =>
    intro s2' htr
    unfold lts at *
    cases htr
    case parL p q r p' htr =>
      cases htr
      case parL p q r p' _ =>
        exists p'.par (q.par r)
        grind
      case parR p q r q' _ =>
        exists p.par (q'.par r)
        grind
      case com μ p' μ' q' _ htrp htrq =>
        exists p'.par (q'.par r)
        grind
    case parR p q r r' htr =>
      exists p.par (q.par r')
      grind
    case com p q r μ p' μ' r' _ htr htr' =>
      cases htr
      case parL p' _ =>
        use p'.par (q.par r')
        grind
      case parR q' _ =>
        use p.par (q'.par r')
        grind
      case com => grind
  case left.assoc =>
    intro s2' htr
    unfold lts at *
    cases htr
    case parR htr =>
      cases htr
      case parL p q r q' _ =>
        exists (p.par q').par r
        grind
      case parR p q r r' _ =>
        exists (p.par q).par r'
        grind
      case com p q r μ q' μ' r' _ htrp htrq =>
        use (p.par q').par r'
        grind
    case parL p q r p' htr =>
      exists (p'.par q).par r
      grind
    case com p q r μ p' μ' q' _ htr htr' =>
      cases htr'
      case parL q' _ =>
        use (p'.par q').par r
        grind
      case parR r' _ =>
        use (p'.par q).par r'
        grind
      case com => grind
  all_goals grind