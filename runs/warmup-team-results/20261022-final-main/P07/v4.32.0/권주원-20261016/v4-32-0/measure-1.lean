/-
Copyright (c) 2025 Chris Henson. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Chris Henson
-/

module

public import Lean
public import Cslib.Languages.LambdaCalculus.LocallyNameless.Fsub.Typing

open Lean Elab Command in
elab "#refactor_eval " tag:str target:str cmd:command : command =>
  show CommandElabM Unit from do
    let name := target.getString.toName
    if (← getEnv).contains name then
      throwError "evaluation target already exists before candidate"
    let start ← IO.getNumHeartbeats
    elabCommand cmd
    let finish ← IO.getNumHeartbeats
    let env ← getEnv
    unless env.contains name do
      throwError "candidate did not define evaluation target"
    let axioms ← Lean.collectAxioms name
    let report := Json.mkObj [
      ("target", toJson target.getString),
      ("raw", toJson (finish - start)),
      ("scaled", toJson ((finish - start) / 1000)),
      ("axioms", toJson (axioms.toList.map Name.toString))]
    logInfo m!"REFACTOR_EVAL {tag.getString} {report.compress}"


/-! # λ-calculus

The λ-calculus with polymorphism and subtyping, with a locally nameless representation of syntax.
This file proves type safety.

## References

* [A. Chargueraud, *The Locally Nameless Representation*][Chargueraud2012]
* See also <https://www.cis.upenn.edu/~plclub/popl08-tutorial/code/>, from which
  this is adapted

-/

public section

namespace Cslib

variable {Var : Type*} [HasFresh Var] [DecidableEq Var]

namespace LambdaCalculus.LocallyNameless.Fsub

open Context List Env.Wf Term Ty

variable {t : Term Var}

/-- Any reduction step preserves typing. -/
lemma Typing.preservation (der : Typing Γ t τ) (step : t ⭢βᵛ t') : Typing Γ t' τ := by
  induction der generalizing t'
  case app Γ _ σ τ _ _ _ _ _ =>
    cases step
    case appₗ | appᵣ => grind
    case abs der _ _ =>
      have sub : Sub Γ (σ.arrow τ) (σ.arrow τ) := by grind [Sub.refl]
      have ⟨_, _, ⟨_, _⟩⟩ := der.abs_inv sub
      grind [fresh_exists <| free_union [fvTm] Var, openTm_substTm_intro, subst_tm, Sub.weaken]
  case tapp Γ _ σ τ σ' _ _ _ =>
    cases step
    case tabs der _ _ =>
      have sub : Sub Γ (σ.all τ) (σ.all τ) := by grind [Sub.refl]
      have ⟨_, _, ⟨_, _⟩⟩ := der.tabs_inv sub
      have ⟨X, mem⟩ := fresh_exists <| free_union [Ty.fv, fvTy] Var
      simp at mem
      have : Γ = (Context.mapVal (·[X := σ']) []) ++ Γ := by grind
      rw [openTy_substTy_intro (X := X), open_subst_intro (X := X)] <;> grind [subst_ty]
    case tapp => grind
  case let' Γ _ _ _ _ L der _ ih₁ _ =>
    cases step
    case let_bind red₁ _ => apply Typing.let' L (ih₁ red₁); grind
    case let_body =>
      grind [fresh_exists <| free_union [fvTm] Var, openTm_substTm_intro, subst_tm]
  case case Γ _ σ τ _ _ _ L _ _ _ ih₁ _ _ =>
    have sub : Sub Γ (σ.sum τ) (σ.sum τ) := by grind [Sub.refl]
    have : Γ = [] ++ Γ := by rfl
    cases step
    case «case» red₁ _ _ => apply Typing.case L (ih₁ red₁) <;> grind
    case case_inl der _ _ =>
      have ⟨_, ⟨_, _⟩⟩ := der.inl_inv sub
      grind [fresh_exists <| free_union [fvTm] Var, openTm_substTm_intro, subst_tm]
    case case_inr der _ _ =>
      have ⟨_, ⟨_, _⟩⟩ := der.inr_inv sub
      grind [fresh_exists <| free_union [fvTm] Var, openTm_substTm_intro, subst_tm]
  all_goals grind [cases Red]

set_option Elab.async false in
#refactor_eval "3c51b2fea2b34ec1a487104656b57d51" "Cslib.LambdaCalculus.LocallyNameless.Fsub.Typing.progress"
set_option linter.tacticAnalysis.verifyGrindOnly false in
/-- Any typable term either has a reduction step or is a value. -/
lemma Typing.progress (der : Typing [] t τ) : t.Value ∨ ∃ t', t ⭢βᵛ t' := by
  generalize eq : [] = Γ at der
  let lc := der.wf.2.1
  induction der <;> subst eq
  case var mem => simp at mem
  case app l r il ir =>
    right
    rcases il rfl with vl | ⟨t', hl⟩
    · rcases ir rfl with vr | ⟨t', hr⟩
      · obtain ⟨_, _, rfl⟩ := l.canonical_form_abs vl
        exact ⟨_, .abs vl.lc vr⟩
      · exact ⟨_, .appᵣ vl hr⟩
    · exact ⟨_, .appₗ r.wf.2.1 hl⟩
  case tapp der sub ih =>
    right
    rcases ih rfl with v | ⟨t', h⟩
    · obtain ⟨_, _, rfl⟩ := der.canonical_form_tabs v
      exact ⟨_, .tabs v.lc sub.wf.2.1.lc⟩
    · exact ⟨_, .tapp sub.wf.2.1.lc h⟩
  case let' ih _ =>
    right
    have hb := (body_let.mp lc).2
    rcases ih rfl with v | ⟨t', h⟩ <;>
      solve_by_elim [Exists.intro, Red.let_body, Red.let_bind]
  case inl ih | inr ih =>
    rcases ih rfl with v | ⟨_, h⟩ <;>
      solve_by_elim [Or.inl, Or.inr, Exists.intro, Value.inl, Value.inr, Red.inl, Red.inr]
  case case der _ _ ih _ _ =>
    right
    obtain ⟨_, hb₂, hb₃⟩ := body_case.mp lc
    rcases ih rfl with v | ⟨t', h⟩
    · obtain ⟨t', rfl | rfl⟩ := der.canonical_form_sum v
      all_goals cases v
      all_goals apply_rules [Exists.intro, Term.Red.case_inl, Term.Red.case_inr]
    · exact ⟨_, .case h hb₂ hb₃⟩
  all_goals first
  | left; constructor; exact lc
  | rename_i ih; exact ih rfl



end LambdaCalculus.LocallyNameless.Fsub

end Cslib
