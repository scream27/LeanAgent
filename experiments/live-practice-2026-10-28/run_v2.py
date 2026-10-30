"""Preserve failed original runs; fix ambiguous command/tactic wrapper boundary."""
import sys,json,re
from pathlib import Path
from run import HERE,REPO,LiveEvaluator,lean,harness,mod
BASE_RENDER=mod.compatible_render

def render_v2(template,code,name,nonce):
 source=BASE_RENDER(template,code,name,nonce)
 if nonce is not None:
  # Start with an unambiguously top-level # command. The option belongs to
  # the enclosed target command, so the proof still elaborates synchronously.
  pattern=r'(set_option Elab\.async false in\n)(#refactor_eval [^\n]+\n)'
  source,count=re.subn(pattern,lambda m:m[2]+m[1],source,count=1)
  if count!=1:raise ValueError('Expected one measurement wrapper')
 return source
class V2Evaluator(LiveEvaluator):
 def _evaluate_environment(self,*args,**kwargs):
  saved=lean.render
  try:
   lean.render=render_v2
   return super(LiveEvaluator,self)._evaluate_environment(*args,**kwargs)
  finally:lean.render=saved
 def fingerprint(self,env):
  v=super().fingerprint(env);v['boundary_fix_sha256']=lean.sha256(Path(__file__).read_bytes());return v

def run(n):
 d=HERE/'inputs'/str(n);root=REPO/'runs/live-practice-2026-10-28'/str(n);out=root/'raw-v2'
 if out.exists():raise FileExistsError(out)
 cfg=harness.read(d/'config.json');cfg['model']['exchange_directory']=str(root/'exchange-v2');path=d/'config-v2.json';harness.write(path,cfg)
 env=harness.read(d/'environment.json')
 try:
  s=harness.run(path,out,evaluator=V2Evaluator(Path(env['project'])));harness.write(root/'replay-v2.json',harness.replay(out));print('COMPLETE-V2',n,s['final_valid'],flush=True)
 except Exception as e:
  harness.write(root/'run-error-v2.json',{'type':type(e).__name__,'message':str(e)});print('FAILED-V2',n,type(e).__name__,str(e),flush=True)
if __name__=='__main__':
 for n in map(int,sys.argv[1:]):run(n)
