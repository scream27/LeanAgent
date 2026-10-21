/- Inspect original compiled theorem constants and their transitive axioms.
   Run under `lake env lean --run` in the pinned Strata checkout.
   This does not validate rewritten proofs. Imports use trust level zero.
-/
import Lean

open Lean

def rangeJson (r : DeclarationRange) : Json := Json.mkObj [
  ("start_line", toJson r.pos.line), ("start_column", toJson r.pos.column),
  ("end_line", toJson r.endPos.line), ("end_column", toJson r.endPos.column)]

unsafe def main (args : List String) : IO UInt32 := do
  initSearchPath ((← IO.appPath).parent.get!.parent.get!)
  enableInitializersExecution
  let modules := args.map String.toName
  let env ← importModules (loadExts := true) (modules.toArray.map fun n =>
    { module := n, importAll := true }) {}
  let mut rows : Array (String × Json) := #[]
  for (name, info) in env.constants.toList do
    unless info matches .thmInfo _ do continue
    let some idx := env.getModuleIdxFor? name | continue
    let modName := env.allImportedModuleNames[idx]!
    unless modules.contains modName do continue
    let (_, axioms) := ((CollectAxioms.collect name).run env).run {}
    let range := declRangeExt.find? (level := .exported) env name <|>
      declRangeExt.find? (level := .server) env name
    let row := Json.mkObj [
      ("kernel_name", toJson name.toString),
      ("user_name", toJson (privateToUserName name).toString),
      ("module", toJson modName.toString),
      ("kind", toJson "theorem"),
      ("axioms", toJson (axioms.axioms.map Name.toString)),
      ("has_sorryAx", toJson (axioms.axioms.contains ``sorryAx)),
      ("declaration_range", range.map (rangeJson ·.range) |>.getD Json.null),
      ("selection_range", range.map (rangeJson ·.selectionRange) |>.getD Json.null)]
    rows := rows.push (name.toString, row)
  for (_, row) in rows.qsort (fun a b => a.1 < b.1) do
    IO.println row.compress
  return 0
