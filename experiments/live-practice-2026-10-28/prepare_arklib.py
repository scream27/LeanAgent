"""Pinned ArkLib preparation; fetch only the dependencies needed by gate-valid inputs."""
import os,sys,json,subprocess,re
from pathlib import Path
from setup import HERE,REPO,prepare_input
sys.path.insert(0,str(REPO/'src'))
from lean_agent.evaluator.tokens import validate_declaration,without_comments
S=REPO/'artifacts/live-practice/arklib-v4.31.0';P=S/'project';logs=HERE/'setup-logs/arklib-v4.31.0';logs.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,ELAN_HOME=str(S/'elan'),XDG_CACHE_HOME=str(S/'cache'));lake=str(Path.home()/'.elan/bin/lake')
def call(label,args):
 print('START',label,flush=True)
 with (logs/(label+'.log')).open('w') as f:r=subprocess.run(args,cwd=P,env=env,stdout=f,stderr=subprocess.STDOUT)
 print('END',label,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(label)
rows=[x for x in json.loads((HERE/'manifest.json').read_text())['problems'] if x['row']['source']=='arklib'];valid=[]
for x in rows:
 try:validate_declaration(x['row']['src'],x['row']['statement']);valid.append(x)
 except ValueError:pass
call('dependencies',[lake,'env','true'])
roots=[P,*[x for x in (P/'.lake/packages').iterdir() if x.is_dir()]];todo=[x['row']['file_path'][:-5].replace('/','.') for x in valid];seen=set();cache=set();missing=[]
while todo:
 mod=todo.pop()
 if mod in seen:continue
 seen.add(mod)
 if mod.startswith(('Mathlib.','Batteries.')) or mod in ('Mathlib','Batteries','Qq','Aesop'):cache.add(mod);continue
 if mod.startswith(('Lean.','Init.','Std.')) or mod in ('Lean','Init','Std'):continue
 files=[root/(mod.replace('.','/')+'.lean') for root in roots];f=next((f for f in files if f.exists()),None)
 if f is None:missing.append(mod);continue
 for line in without_comments(f.read_text()).splitlines():
  q=re.match(r'^(?:public |private |meta )?import (?:all )?(.+)$',line)
  if q:todo.extend(q[1].split())
(HERE/'arklib-cache-plan.json').write_text(json.dumps({'visited_modules':len(seen),'cache_roots':sorted(cache),'missing':missing,'build_ids':[x['id'] for x in valid]},indent=2))
if missing:raise RuntimeError('Unresolved import roots: '+str(missing))
call('cache-targeted',[lake,'exe','cache','get',*sorted(cache)])
call('build-targeted',[lake,'build',*sorted({x['row']['file_path'][:-5].replace('/','.') for x in valid})])
for x in rows:prepare_input(x,P,[sys.executable,str(HERE/'lean_env.py'),str(S/'elan'),str(S/'cache'),'-j1'])
(HERE/'arklib-v4.31.0-ready.json').write_text(json.dumps({'project':str(P),'ids':[x['id'] for x in rows],'built_ids':[x['id'] for x in valid]}))
