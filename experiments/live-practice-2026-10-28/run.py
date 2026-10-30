import json,sys,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(REPO/'experiments/repair-bridge-2026-10-27'))
from bridge import PreparedEvaluator
from lean_agent import harness
from lean_agent.evaluator import lean
spec=importlib.util.spec_from_file_location('expansion_adapter',REPO/'experiments/harness-expansion-2026-10-27/run.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class LiveEvaluator(PreparedEvaluator):
 def _evaluate_environment(self,*args,**kwargs):
  saved=lean.render
  try:
   lean.render=mod.compatible_render
   return super()._evaluate_environment(*args,**kwargs)
  finally:lean.render=saved
 def fingerprint(self,env):
  value=super().fingerprint(env);value['live_adapter_sha256']=lean.sha256(Path(__file__).read_bytes());value['measurement_adapter_sha256']=lean.sha256(Path(mod.__file__).read_bytes());return value

def run(n):
 d=HERE/'inputs'/str(n);out=REPO/'runs/live-practice-2026-10-28'/str(n)/'raw'
 if out.exists():
  if (out/'summary.json').exists():return
  raise RuntimeError('Existing interrupted run: preserve before restarting')
 env=json.loads((d/'environment.json').read_text())
 try:
  summary=harness.run(d/'config.json',out,evaluator=LiveEvaluator(Path(env['project'])))
  harness.write(out.parent/'replay.json',harness.replay(out));print('COMPLETE',n,summary['final_valid'],flush=True)
 except Exception as e:
  print('FAILED',n,type(e).__name__,str(e),flush=True)
  harness.write(out.parent/'run-error.json',{'type':type(e).__name__,'message':str(e)})
if __name__=='__main__':
 for n in map(int,sys.argv[1:]):run(n)
