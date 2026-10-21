/-
Syntax audit for the Strata corpus, using the pinned Lean parser.

Run with the exact toolchain executable (the source project need not be built):
  /path/to/lean-4.26.0/bin/lean --run scripts/ExtractDeclarations.lean FILE...

One JSON object is emitted per input file. All byte ranges are UTF-8, half-open.
This parses but does not elaborate, type-check, resolve names, or measure heartbeat.
The default environment loads Lean's standard syntax only. Project/local custom
syntax may cause recovery, truncated declarations, and omissions: inspect `errors`
and compare against an independent lexical inventory. `--source-imports` loads
built project imports through LEAN_PATH, but still does not execute local syntax
commands. Add --syntax-module=MODULE to load syntax from another built module
(e.g. the source module itself, when it defines syntax used in its own proofs).
This must not be described as compilation validation.
-/
import Lean

open Lean Parser

namespace ExtractDeclarations

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
partial def theoremNodes (stx : Syntax) : Array (Syntax × Syntax) :=
  if stx.isOfKind ``Command.declaration && stx[1].isOfKind ``Command.theorem then
    #[(stx, stx[1])]
  else if stx.isOfKind ``Command.theorem then #[(stx, stx)]
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
    ("namespace_syntactic", toJson namespaceParts),
    ("root_command_range", rangeJson rootCommand),
    ("command_range", rangeJson command),
    ("declaration_range", rangeJson decl),
    ("statement_range", statementRange),
    ("value_range", rangeJson val),
    ("assignment_range", if simple then rangeJson val[0] else Json.null),
    ("proof_range", rangeJson proof),
    ("proof_kind", toJson proof.getKind.toString),
    ("value_kind", toJson val.getKind.toString),
    ("has_missing_syntax", toJson (containsMissing command)),
    ("source_name", toJson (sourceText source decl[1]))]

unsafe def inspectFile (baseEnv : Environment) (path : String) (sourceImports : Bool) (syntaxModules : Array Import) : IO Json := do
  let source ← IO.FS.readFile path
  let ctx := mkInputContext source path
  let (header, initState, headerMessages) ← parseHeader ctx
  let env ← if sourceImports then
    importModules (loadExts := true) ((Elab.headerToImports header ++ syntaxModules).push {module := `Lean}) {}
    else pure baseEnv
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
    let (stx, next, newMessages) := parseCommand ctx {env := env, options := {}} state messages
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
    if state.pos == previousPos then break
  let mut errors : Array Json := #[]
  for msg in messages.toList do
    errors := errors.push (Json.mkObj [
      ("line", toJson msg.pos.line), ("column", toJson msg.pos.column),
      ("severity", toJson (match msg.severity with | .error => "error" | .warning => "warning" | .information => "information")),
      ("message", toJson (← msg.data.toString))])
  return Json.mkObj [
    ("path", toJson path),
    ("parser", toJson "Lean 4.26.0 native command parser"),
    ("environment", toJson (if sourceImports then "source_imports_plus_Lean" else "Lean_builtin_syntax")),
    ("extra_syntax_modules", toJson (syntaxModules.map fun i => i.module.toString)),
    ("elaborated", toJson false),
    ("header_range", rangeJson header.raw),
    ("reached_terminal", toJson stopped),
    ("declarations", toJson declarations),
    ("commands", toJson commands),
    ("errors", toJson errors)]

end ExtractDeclarations

unsafe def main (args : List String) : IO UInt32 := do
  if args.isEmpty then
    IO.eprintln "Usage: lean --run scripts/ExtractDeclarations.lean [--source-imports] [--syntax-module=MODULE] FILE..."
    return 1
  -- IO.appPath is the real Lean executable. findSysroot would invoke `lean`
  -- through PATH, potentially selecting an unrelated elan toolchain.
  initSearchPath ((← IO.appPath).parent.get!.parent.get!)
  enableInitializersExecution
  let syntaxModules := (args.filterMap fun arg =>
    if arg.startsWith "--syntax-module=" then
      some ({module := (arg.drop 16).toName} : Import)
    else none).toArray
  let env ← importModules (loadExts := true) (syntaxModules.push {module := `Lean}) {}
  let sourceImports := args.contains "--source-imports"
  let mut failed := false
  for path in args.filter (fun arg => arg != "--source-imports" && !arg.startsWith "--syntax-module=") do
    try
      IO.println (← ExtractDeclarations.inspectFile env path sourceImports syntaxModules).compress
    catch e =>
      failed := true
      IO.println (Json.mkObj [("path", toJson path), ("fatal_error", toJson e.toString)]).compress
  return if failed then 1 else 0
