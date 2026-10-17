module
import Lean
public import Lean

elab "#arena_count " cmd:command : command => do
  let start ← IO.getNumHeartbeats
  Lean.Elab.Command.elabCommand (← `(command| set_option Elab.async false in $cmd))
  let finish ← IO.getNumHeartbeats
  Lean.logInfo m!"ARENA_HEARTBEATS_RAW={finish - start}"

#arena_count
public theorem smoke : True := by trivial
