/-
Syntax audit for the PhysLib corpus, using the pinned Lean parser.

Run with the exact toolchain executable (the source project need not be built):
  /path/to/lean-4.32.0/bin/lean --run scripts/ExtractPhyslibDeclarations.lean FILE...

One JSON object is emitted per input file. All byte ranges are UTF-8, half-open.
Declarations and proofs are parsed, never elaborated, type-checked, or timed.
Names are syntactically qualified, not kernel-resolved.
The default environment loads Lean's standard syntax only. Project/local custom
syntax may cause recovery, truncated declarations, and omissions: inspect `errors`
and compare against an independent lexical inventory. `--source-imports` loads
built project imports through LEAN_PATH. --local-syntax elaborates only scope,
notation, mixfix, and syntax setup commands; its diagnostics are separately
recorded in syntax_setup_errors. Add --syntax-module=MODULE to load syntax from another built module
(e.g. the source module itself, when it defines syntax used in its own proofs).
Use --syntax-module=Mathlib.Tactic.Lemma for synthetic lemma fixtures, or
--syntax-module=Mathlib for a broad math syntax baseline. Run through the pinned
project lake env so LEAN_PATH contains built dependencies. Parser errors and
missing nodes must be quarantined, never used as exact proof boundaries.
This must not be described as compilation validation.
-/
import Lean.Elab.Command
import Lean.Elab.Import
import Lean.Elab.Syntax
import Lean.Elab.Notation
import Lean.Elab.Mixfix

open Lean Parser

namespace ExtractPhyslibDeclarations

def rangeJson (stx : Syntax) : Json :=
  match stx.getPos?, stx.getTailPos? with
  | some start, some stop => Json.mkObj [
      ("start_byte", toJson start.byteIdx), ("end_byte", toJson stop.byteIdx)]
  | _, _ => Json.null

def sourceText (source : String) (stx : Syntax) : String :=
  match stx.getPos?, stx.getTailPos? with
  | some start, some stop => String.Pos.Raw.extract source start stop
  | _, _ => ""

partial def containsMissing (stx : Syntax) : Bool :=
  stx.isMissing || stx.getArgs.any containsMissing

/-- Descend only command-bearing wrappers, never term/tactic quotations. -/
def isProofDeclaration (stx : Syntax) : Bool :=
  stx.isOfKind ``Command.theorem

partial def theoremNodes (stx : Syntax) : Array (Syntax × Syntax) :=
  if stx.isOfKind ``Command.declaration && isProofDeclaration stx[1] then
    #[(stx, stx[1])]
  else if stx.getKind == `lemma || stx.getKind == `Batteries.Tactic.Lemma.lemmaCmd then
    #[(stx, stx[1])]
  else if isProofDeclaration stx then #[(stx, stx)]
  else if stx.isOfKind ``Command.in then
    theoremNodes stx[2]
  else if stx.isOfKind ``Command.mutual then
    stx[1].getArgs.foldl (fun acc child => acc ++ theoremNodes child) #[]
  else #[]

def declarationJson (source : String) (rootCommand command decl : Syntax) (namespaceParts : Array String) : Json := Id.run do
  let val := decl[3]
  let simple := val.isOfKind ``Command.declValSimple
  let proof := if simple then val[1] else val
  let statementRange := match decl.getPos?, val.getPos? with
    | some start, some stop => Json.mkObj [
        ("start_byte", toJson start.byteIdx), ("end_byte", toJson stop.byteIdx)]
    | _, _ => Json.null
  return Json.mkObj [
    ("name", toJson decl[1][0].getId.toString),
    ("declaration_kind", toJson (if decl[0].getAtomVal == "lemma" then "lemma" else "theorem")),
    ("namespace_syntactic", toJson namespaceParts),
    ("root_command_range", rangeJson rootCommand),
    ("command_range", rangeJson command),
    ("declaration_range", rangeJson decl),
    ("statement_range", statementRange),
    ("value_range", rangeJson val),
    ("assignment_range", if simple then rangeJson val[0] else Json.null),
    ("proof_range", rangeJson proof),
    ("proof_with_suffix_range", match proof.getPos?, val.getTailPos? with
      | some start, some stop => Json.mkObj [
          ("start_byte", toJson start.byteIdx), ("end_byte", toJson stop.byteIdx)]
      | _, _ => Json.null),
    ("termination_suffix_range", if simple then rangeJson val[2] else Json.null),
    ("where_declarations_range", if simple then rangeJson val[3] else Json.null),
    ("proof_kind", toJson proof.getKind.toString),
    ("value_kind", toJson val.getKind.toString),
    ("has_missing_syntax", toJson (containsMissing command)),
    ("source_name", toJson (sourceText source decl[1]))]

/-- Only syntax/scope setup is elaborated; declarations and proofs are never elaborated. -/
def isSyntaxSetup (stx : Syntax) : Bool :=
  [``Command.namespace, ``Command.section, ``Command.end, ``Command.open,
   ``Command.syntax, ``Command.syntaxCat, ``Command.notation,
   ``Command.mixfix].contains stx.getKind

unsafe def inspectFile (baseEnv : Environment) (path : String) (sourceImports localSyntax : Bool) (syntaxModules : Array Import) : IO Json := do
  let source ← IO.FS.readFile path
  let ctx := mkInputContext source path
  let (header, initState, headerMessages) ← parseHeader ctx
  let env ← if sourceImports then
    importModules (loadExts := true) ((Elab.headerToImports header ++ syntaxModules).push {module := `Lean}) {}
    else pure baseEnv
  let mut commandState := Elab.Command.mkState env
  let mut syntaxSetupErrors : Array Json := #[]
  let mut state := initState
  let mut messages := headerMessages
  let mut declarations : Array Json := #[]
  let mut commands : Array Json := #[]
  let mut scope : Array (Bool × String) := #[]
  let mut stopped := false
  -- Every successful iteration consumes source or reaches EOF. This extra ceiling
  -- only protects the audit from unexpected parser recovery behavior.
  for _ in [:source.utf8ByteSize + 1] do
    let previousPos := state.pos
    let (stx, next, newMessages) := parseCommand ctx {
      env := commandState.env, options := commandState.scopes.head!.opts,
      currNamespace := commandState.scopes.head!.currNamespace,
      openDecls := commandState.scopes.head!.openDecls} state messages
    state := next
    messages := newMessages
    if isTerminalCommand stx then
      stopped := true
      break
    commands := commands.push (Json.mkObj [
      ("kind", toJson stx.getKind.toString), ("range", rangeJson stx),
      ("has_missing_syntax", toJson (containsMissing stx))])
    for (innerCommand, decl) in theoremNodes stx do
      declarations := declarations.push (declarationJson source stx innerCommand decl
        (scope.filterMap fun (isNamespace, name) => if isNamespace then some name else none))
    if stx.isOfKind ``Command.namespace then
      scope := scope.push (true, stx[1].getId.toString)
    else if stx.isOfKind ``Command.section then
      scope := scope.push (false, "")
    else if stx.isOfKind ``Command.end then
      scope := scope.pop
    if localSyntax && isSyntaxSetup stx && !containsMissing stx then
      let commandCtx : Elab.Command.Context := {
        fileName := path, fileMap := ctx.fileMap, cmdPos := previousPos,
        snap? := none, cancelTk? := none }
      let before := commandState
      match ← EIO.toIO' <| ((Elab.Command.elabCommand stx) commandCtx).run commandState with
      | .ok (_, updated) =>
        commandState := {updated with messages := {}}
        for msg in updated.messages.toList do
          syntaxSetupErrors := syntaxSetupErrors.push (Json.mkObj [
            ("line", toJson msg.pos.line), ("column", toJson msg.pos.column),
            ("message", toJson (← msg.data.toString))])
      | .error e =>
        commandState := before
        syntaxSetupErrors := syntaxSetupErrors.push (Json.mkObj [
          ("range", rangeJson stx), ("message", toJson (← e.toMessageData.toString))])
    if state.pos == previousPos then break
  let mut errors : Array Json := #[]
  for msg in messages.toList do
    errors := errors.push (Json.mkObj [
      ("line", toJson msg.pos.line), ("column", toJson msg.pos.column),
      ("severity", toJson (match msg.severity with | .error => "error" | .warning => "warning" | .information => "information")),
      ("message", toJson (← msg.data.toString))])
  return Json.mkObj [
    ("path", toJson path),
    ("parser", toJson "Lean 4.32.0 native command parser"),
    ("source_byte_size", toJson source.utf8ByteSize),
    ("environment", toJson (if sourceImports then "source_imports_plus_Lean" else if syntaxModules.isEmpty then "Lean_builtin_syntax" else "Lean_plus_syntax_modules")),
    ("extra_syntax_modules", toJson (syntaxModules.map fun i => i.module.toString)),
    ("elaborated", toJson false),
    ("syntax_commands_elaborated", toJson localSyntax),
    ("syntax_setup_errors", toJson syntaxSetupErrors),
    ("header_range", rangeJson header.raw),
    ("reached_terminal", toJson stopped),
    ("declarations", toJson declarations),
    ("commands", toJson commands),
    ("errors", toJson errors)]

end ExtractPhyslibDeclarations

unsafe def main (args : List String) : IO UInt32 := do
  if args.isEmpty then
    IO.eprintln "Usage: lean --run scripts/ExtractPhyslibDeclarations.lean [--source-imports] [--local-syntax] [--syntax-module=MODULE] FILE..."
    return 1
  -- IO.appPath is the real Lean executable. findSysroot would invoke `lean`
  -- through PATH, potentially selecting an unrelated elan toolchain.
  let sysroot ← match ← IO.getEnv "PHYSLIB_LEAN_SYSROOT" with
    | some value => pure (System.FilePath.mk value)
    | none => pure ((← IO.appPath).parent.get!.parent.get!)
  initSearchPath sysroot
  enableInitializersExecution
  let syntaxModules := (args.filterMap fun arg =>
    if arg.startsWith "--syntax-module=" then
      some ({module := (arg.drop 16).toName} : Import)
    else none).toArray
  let sourceImports := args.contains "--source-imports"
  let env ← if sourceImports then mkEmptyEnvironment else
    importModules (loadExts := true) (syntaxModules.push {module := `Lean}) {}
  let localSyntax := args.contains "--local-syntax"
  let mut failed := false
  for path in args.filter (fun arg => arg != "--source-imports" && arg != "--local-syntax" && !arg.startsWith "--syntax-module=") do
    try
      IO.println (← ExtractPhyslibDeclarations.inspectFile env path sourceImports localSyntax syntaxModules).compress
    catch e =>
      failed := true
      IO.println (Json.mkObj [("path", toJson path), ("fatal_error", toJson e.toString)]).compress
  return if failed then 1 else 0
