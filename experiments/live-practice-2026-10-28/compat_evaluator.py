"""Compatibility-only fix: keep Lake stderr out of --print-prefix stdout."""
from pathlib import Path
from run_v2 import V2Evaluator
from run import lean
class CompatibilityEvaluator(V2Evaluator):
 def fingerprint(self,env):
  execute=lean.execute
  diagnostics=[]
  def separated(command,*args,**kwargs):
   if command[-1:] == ['--print-prefix']:
    kwargs['separate_stderr']=True
    result=execute(command,*args,**kwargs)
    diagnostics.append({'command':command,'stdout':result['output'],'stderr':result['stderr']})
    return result
   return execute(command,*args,**kwargs)
  try:
   lean.execute=separated
   result=super().fingerprint(env)
  finally:lean.execute=execute
  result['prefix_stderr_adapter_sha256']=lean.sha256(Path(__file__).read_bytes())
  result['prefix_diagnostics']=diagnostics
  return result
