"""Pinned ArkLib preparation; fetch only the dependencies needed by gate-valid inputs."""
import os,sys,json,subprocess,re
from pathlib import Path
from setup import HERE,REPO,prepare_input
sys.path.insert(0,str(REPO/'src'))
from lean_agent.evaluator.tokens import validate_declaration,without_comments
version=sys.argv[1]
S=REPO/'artifacts/live-practice'/('arklib-'+version);P=S/'project';S.mkdir(parents=True,exist_ok=True);logs=HERE/'setup-logs'/('arklib-'+version);logs.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,ELAN_HOME=str(S/'elan'),XDG_CACHE_HOME=str(S/'cache'));lake=str(Path.home()/'.elan/bin/lake')
def call(label,args,cwd=P):
 print('START',label,flush=True)
 with (logs/(label+'.log')).open('w') as f:r=subprocess.run(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 print('END',label,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(label)
rows=[x for x in json.loads((HERE/'manifest.json').read_text())['problems'] if x['id']==12];valid=[]
pin=next(v[version] for v in rows[0]['row']['version_info'] if version in v)
if not P.exists():call('clone',['git','clone','--shared',str(REPO/'artifacts/live-practice/arklib-v4.31.0/project'),str(P)],REPO)
if subprocess.run(['git','cat-file','-e',pin+'^{commit}'],cwd=P,capture_output=True).returncode:call('fetch',['git','fetch','--depth','1',rows[0]['row']['url'],pin])
call('checkout',['git','checkout','--detach',pin])
if not (S/'instructions-reviewed').exists():print('REVIEW_INSTRUCTIONS',P,flush=True);raise SystemExit(10)
for x in rows:
 f=P/x['row']['file_path']
 if not f.exists() or f.read_text().count(x['row']['src'])!=1:raise RuntimeError('Reference/context mismatch '+version)
call('toolchain',[str(Path.home()/'.elan/bin/elan'),'toolchain','install','leanprover/lean4:'+version])
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
(HERE/('arklib-'+version+'-cache-plan.json')).write_text(json.dumps({'visited_modules':len(seen),'cache_roots':sorted(cache),'missing':missing,'build_ids':[x['id'] for x in valid]},indent=2))
if missing:raise RuntimeError('Unresolved import roots: '+str(missing))
call('cache-targeted',[lake,'exe','cache','get',*sorted(cache)])
call('build-targeted',[lake,'build',*sorted({x['row']['file_path'][:-5].replace('/','.') for x in valid})])
(HERE/('arklib-'+version+'-compat-ready.json')).write_text(json.dumps({'project':str(P),'ids':[x['id'] for x in rows],'built_ids':[x['id'] for x in valid]}))
