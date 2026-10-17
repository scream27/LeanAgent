"""Materialize model-authored, one-shot edits BEFORE Lean feedback.

This is a reproducible record of this chat model's outputs, not an API generator.
No verification-driven edits are permitted after the freeze.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = [json.loads(l) for l in (HERE / 'reference' / 'benchmark_data_warmup.jsonl').read_text().splitlines()]


def replace(s, a, b):
    assert a in s, repr(a)
    return s.replace(a, b)


def between(s, a, b, replacement):
    i, j = s.index(a), s.index(b, s.index(a))
    return s[:i] + replacement + s[j:]


def propose(n, p, s):
    if n == 8:
        return s, 'User explicitly excluded recursive theorem from refactoring pending policy review.'
    if n == 1:
        if p == 1:
            for block in ['    simp at m\n    simp at name\n    simp at ty2\n', '    simp at m\n    simp at name\n', '    simp at m\n']:
                s = s.replace(block, '')
            return s, 'Remove simplification of metadata variables in base cases.'
        if p == 2:
            return 'by\n  induction post <;> simp_all [substOld, Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars, List.subset_def]\n  all_goals repeat first | split | progress simp_all\n', 'Combine recursive subset reasoning; exploratory candidate informed by prior exposure.'
        s = replace(s, 'apply ih1 <;> assumption', 'exact ih1')
        s = replace(s, 'apply ih2 <;> assumption', 'exact ih2')
        return s, 'Replace assumption dispatch with direct induction-hypothesis applications.'
    if n == 2:
        if p == 1:
            return replace(s, '      intros x Hin\n      exact Hin', '      exact fun _ hx => hx'), 'Use the identity function for the unchanged variable membership.'
        if p == 2:
            return 'by\n  intro hn\n  induction hn <;> simp_all [extractOldExprVars, Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars, List.subset_def]\n  all_goals repeat first | split | progress simp_all\n', 'Induct on normalization evidence and combine branch reasoning; prior exposure noted.'
        return replace(s, 'apply fn_ih\n        exact H1', 'exact fn_ih H1').replace('apply e_ih\n        exact H2', 'exact e_ih H2'), 'Apply induction hypotheses directly.'
    if n == 3:
        if p == 1:
            return replace(s, '  exists (updatedStates σ ks\' vs\')', '  refine ⟨updatedStates σ ks\' vs\', ?_⟩'), 'Make the existential witness explicit with refine.'
        if p == 2:
            s = replace(s, "      . apply (ih Hinit ?_ ?_).2.2\n        . simp [isDefined] at * <;> simp_all\n        . simp_all", "      . exact (ih Hinit (by simp [isDefined] at * <;> simp_all) (by simp_all)).2.2")
            return s, 'Combine the final recursive application with its two premises.'
        return replace(s, '    refine updatedStatesInit Hlen1 ?_ ?_\n    exact InitStatesNotDefined Hinit\n    exact InitStatesNodup Hinit', '    exact updatedStatesInit Hlen1 (InitStatesNotDefined Hinit) (InitStatesNodup Hinit)'), 'Supply known premises directly instead of creating metavariable goals.'
    if n == 4:
        if p == 1:
            return replace(s, 'intro h; apply hx0; exact congrArg (fromL2 ℝ) h', 'intro h; exact hx0 (congrArg (fromL2 ℝ) h)'), 'Combine the nonzero contradiction application.'
        if p == 2:
            s = replace(s, '    have inner_pos_V : ∀ x ∈ Metric.ball x₀ δ₂, 0 < ⟪f x, f x₀⟫_ℝ := fun x hx => inner_pos₂ x hx', '    have inner_pos_V : ∀ x ∈ Metric.ball x₀ δ₂, 0 < ⟪f x, f x₀⟫_ℝ := inner_pos₂')
            return s, 'Eta-reduce the transported positivity lemma.'
        assert s.rstrip().endswith('linarith')
        return s.rstrip()[:-len('linarith')] + 'exact (ne_of_gt integral_pos) key_integral\n', 'Replace final arithmetic search by the explicit positive-versus-zero contradiction.'
    if n == 5:
        if p == 1:
            return replace(s, '      rw [Time.deriv_eq]\n      rw [fderiv_fun_sub]', '      rw [Time.deriv_eq, fderiv_fun_sub]'), 'Combine consecutive rewrites at the same goal.'
        if p == 2:
            return replace(s, '      apply magneticFieldMatrix_contDiff\n      apply hA.of_le (right_eq_inf.mp rfl)', '      exact magneticFieldMatrix_contDiff _ (hA.of_le (right_eq_inf.mp rfl)) _'), 'Replace a two-stage differentiability application with an explicit proof term.'
        return replace(s, '          apply Differentiable.differentiableAt\n          apply LorentzCurrentDensity.chargeDensity_differentiable_space\n          exact hJ.differentiable (by simp)', '          exact (LorentzCurrentDensity.chargeDensity_differentiable_space\n            (hJ.differentiable (by simp)) _ _).differentiableAt'), 'Make the final derivative side condition a direct application.'
    if n == 6:
        if p == 1:
            return replace(s, '      repeat rw [mul_assoc]', '      simp only [mul_assoc]'), 'Normalize associativity in one explicitly scoped simplification.'
        if p == 2:
            return s, 'No confident structural simplification identified without more definition context.'
        return replace(s, '          repeat rw [ofCrAnListF_append]', '          simp only [ofCrAnListF_append]'), 'Use only the append rule instead of repeated rewrite invocation.'
    if n == 7:
        if p == 1:
            return replace(s, '            have ⟨σ, t₁, eq⟩ := l.canonical_form_abs val_l', '            obtain ⟨σ, t₁, eq⟩ := l.canonical_form_abs val_l'), 'Destructure the canonical-form witness directly.'
        if p == 2:
            return s, 'Retain the induction structure; the auxiliary derivation affects induction hypotheses.'
        s = replace(s, '    apply LC.abs L\n    · grind only [→ wf, cases Term.LC]\n    · grind only [→ wf]', '    exact LC.abs L (by grind only [→ wf, cases Term.LC]) (by grind only [→ wf])')
        return s, 'Express the abstraction local-closure proof directly.'
    if n == 9:
        if p == 1:
            return replace(s, '  · constructor; assumption', '  · exact .choice _ _ _ h'), 'Construct the initial choice relation witness directly.'
        if p == 2:
            s = replace(s, "        exists s2'\n        constructor\n        · apply Tr.choiceL htr2\n        · constructor\n          apply hb.le_bisimilarity _ _ hr2", "        exact ⟨s2', Tr.choiceL htr2, .bisim (hb.le_bisimilarity _ _ hr2)⟩")
            s = replace(s, "        exists s1'\n        constructor\n        · apply Tr.choiceL htr1\n        · constructor\n          apply hb.le_bisimilarity _ _ hr1", "        exact ⟨s1', Tr.choiceL htr1, .bisim (hb.le_bisimilarity _ _ hr1)⟩")
            return s, 'Compress the symmetric left-transition witness branches.'
        return replace(s, '          apply HomBisimilarity.refl', '          exact HomBisimilarity.refl'), 'Replace tactic application by direct reflexivity proof.'
    if n == 10:
        if p == 1:
            return replace(s, 'by exact id (Eq.symm h_eq)', 'h_eq.symm'), 'Remove redundant tactic and identity wrappers around equality symmetry.'
        if p == 2:
            return between(s, '    have hS_nonempty : S.Nonempty := by', '    -- For a non-empty set', '    have hS_nonempty : S.Nonempty := Set.image_nonempty.mpr Set.univ_nonempty\n'), 'Collapse the nonempty-image proof to the existing lemma application.'
        return replace(s, 'apply Nat.lt_add_of_pos_right; exact pos_of_neZero 𝓡', 'exact Nat.lt_add_of_pos_right (pos_of_neZero 𝓡)'), 'Directly supply positivity rather than opening an intermediate goal.'
    if n == 11:
        if p == 1:
            return replace(s, '    have h_res := is_fiber_iff_generates_quotient_point', '    have h_res := is_fiber_iff_generates_quotient_point').replace('    rw [h_res]', '    exact h_res'), 'Close the two fiber evaluation equalities directly from their established witnesses.'
        if p == 2:
            a = '    _ = P₀.eval y.val * ((1 - r_chal) * x₁.val - r_chal + r_chal - (1 - r_chal) * x₀.val) +'
            b = '    _ = P₀.eval y.val * ((1 - r_chal) * (x₁.val - x₀.val)) +'
            return between(s, a, b, ''), 'Remove an intermediate ring equality; the following ring step can prove the composed identity.'
        return replace(s, 'by rw [h_fiber_diff]; ring', 'by rw [h_fiber_diff]; simp only [mul_one, one_mul]'), 'Replace ring normalization after substituting a unit difference with the two unit rules.'
    if n == 12:
        if p == 1:
            return replace(s, '        have hϑ : ϑ = ϑ_sub_2 + 1 + 1 := by rfl', '        have hϑ : ϑ = ϑ_sub_2 + 1 + 1 := rfl').replace(':= by rfl', ':= rfl'), 'Remove tactic wrappers from definitional equalities.'
        if p == 2:
            return replace(s, '        apply CA_split_rowwise_implies_CA (u := u) (e := e)\n        exact h_final_gap', '        exact CA_split_rowwise_implies_CA (u := u) (e := e) h_final_gap'), 'Make the final reduction a direct lemma application.'
        return replace(s, '          let res := prob_R_star_gt_threshold', '          exact prob_R_star_gt_threshold').replace('          exact res\n', ''), 'Inline the probability-bound proof instead of introducing an alias.'
    if n == 13:
        if p == 1:
            return replace(s, '            have h₃ : i + (m + 4) ≥ 4 := by\n              have h₄ : i ≥ 0 := by linarith\n              omega', '            have h₃ : i + (m + 4) ≥ 4 := by omega'), 'Remove a redundant nonnegativity lemma before natural arithmetic.'
        if p == 2:
            return between(s, '          | 0 =>', '          | m + 4 =>', '          | 0 => simpa using h_eq.1\n          | 1 => simpa using h_eq.2.1\n          | 2 => simpa using h_eq.2.2.1\n          | 3 => simpa using h_eq.2.2.2\n'), 'Close the four initial recurrence cases from the corresponding tuple components.'
        return replace(s, '          rw [h₆] at h₅\n          rw [h₇] at h₅\n          linarith', '          rw [h₆, h₇] at h₅\n          exact h₅.symm'), 'Replace final integer arithmetic with symmetry of the already proved equality.'
    if n == 14:
        if p == 1:
            return between(s, '    have h₁ : T ∩ T ≠ ∅ :=', '  \n  have h_subset_or_compl', '    exact Set.nonempty_iff_ne_empty.mpr (by simpa using hPP T hT T hT)\n'), 'Derive nonemptiness directly from self-intersection.'
        if p == 2:
            return between(s, '    have h₄ : Fintype.card S ≥ 1 := by', '    have h₅ : P.card =', '    have h₄ : Fintype.card S ≥ 1 := Fintype.card_pos\n'), 'Use the available finite nonempty type cardinality fact directly.'
        return between(s, '  have h_not_both :', '  \n  have h_card', '  have h_not_both : ∀ (A : Set S), A ∈ P → Aᶜ ∉ P := by\n    intro A hA hc\n    exact hPP A hA Aᶜ hc (by simp)\n'), 'Prove complement exclusion without redundant set extensionality and contradiction search.'
    if n == 15:
        if p == 1:
            return replace(s, '    intro i\n    have h₁₀ : 7 ∣ d i - f i := h₉ i\n    exact h₁₀', '    exact h₉'), 'Remove the final eta-expanded proof alias.'
        if p == 2:
            return between(s, '      have h₁₂ : 7 ∣ d i - f i := by', '    \n    intro i', '      simpa only [neg_sub] using (dvd_neg.mpr h₁₁)\n'), 'Collapse nested divisibility and sign-change aliases to one transport.'
        return replace(s, '      have h₁₃ : (7 : ℕ).Prime := by decide', '      have h₁₃ : (7 : ℕ).Prime := by norm_num'), 'Compare arithmetic certification against kernel decision for the prime constant.'
    raise ValueError((n, p))


def main():
    out = HERE / 'candidates.jsonl'
    if out.exists():
        raise SystemExit('Already frozen; refuse overwrite')
    records = []
    for n, r in enumerate(ROWS, 1):
        rest = r['src'][len(r['statement']):]
        assert rest.lstrip().startswith(':=')
        original = rest.lstrip()[2:].lstrip()
        for p in range(1, 4):
            body, reason = propose(n, p, original)
            records.append({'problem_id': n, 'name': r['name'], 'prompt_id': f'P{p}',
                            'original_body': original, 'proof_body': body, 'rationale': reason,
                            'generation': 'chat-model-one-shot-authored-edits-no-API',
                            'prior_exposure': n in (1, 2), 'user_excluded': n == 8,
                            'candidate_hash': hashlib.sha256(body.encode()).hexdigest()})
    out.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in records))
    print('Frozen', len(records), 'candidates before verification')


if __name__ == '__main__':
    main()
