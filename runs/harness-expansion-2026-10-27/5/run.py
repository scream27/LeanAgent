"""Use unchanged common harness; retain raw baseline probes for compatibility failures."""
import json,sys,hashlib,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(REPO/'experiments/repair-bridge-2026-10-27'))
from bridge import PreparedEvaluator
from lean_agent import harness
from lean_agent.evaluator.lean import sha256
from lean_agent.evaluator import lean
ORIGINAL_RENDER=lean.render
def compatible_render(template,code,name,nonce):
 # Only the measurement copy: ordinary comments cannot bind to set_option.
 # Keep normal validation and submitted declarations byte-identical.
 if nonce is not None:
  before,after=template.split("{{DECLARATION}}")
  start=before.rfind("/--")
  if start>=0:
   end=before.find("-/",start)+2
   if end>1 and not before[end:].strip():
    before=before[:start]+"/- "+before[start+3:]
  template=before+"{{DECLARATION}}"+after
 return ORIGINAL_RENDER(template,code,name,nonce)
PROJECT=REPO/'artifacts/harness-expansion/physlib-v4.32.0/project'
class ExpansionEvaluator(PreparedEvaluator):
 def __init__(self):super().__init__(PROJECT)
 def _evaluate_environment(self,*args,**kwargs):
  saved=lean.render
  try:
   lean.render=compatible_render
   return super()._evaluate_environment(*args,**kwargs)
  finally:lean.render=saved
 def fingerprint(self,env):
  value=super().fingerprint(env)
  value['expansion_adapter_sha256']=sha256(Path(__file__).read_bytes())
  value['launcher_sha256']=sha256((HERE/'lean_command.py').read_bytes())
  return value

def run(n):
 out=REPO/'runs/harness-expansion-2026-10-27'/str(n)/'raw-v2'
 if out.exists():
  if (out/'summary.json').exists():return
  raise RuntimeError('Incomplete run preserved; use a new directory')
 summary=harness.run(HERE/'inputs'/str(n)/'config.json',out,evaluator=ExpansionEvaluator())
 harness.write(out.parent/'record-replay.json',harness.replay(out))
 (out.parent/'run.py').write_bytes(Path(__file__).read_bytes())
 print('COMPLETE',n,summary['final_valid'],summary['state']['best']['tokens'],flush=True)
if __name__=='__main__':
 for n in map(int,sys.argv[1:] or ['4','5','6']):run(n)
