by
  rintro -
  refine List.Sublist.subset ?_
  induction post
  case' app => unfold extractOldExprVars; split
  all_goals apply_rules only [*, List.nil_sublist, List.Sublist.append, List.Sublist.refl]
