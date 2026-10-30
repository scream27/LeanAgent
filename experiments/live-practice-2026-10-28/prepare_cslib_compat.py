"""Prepare pinned extra Cslib versions without overwriting primary inputs."""
import os,sys,json,subprocess,re
from pathlib import Path
from setup import HERE,REPO
sys.path.insert(0,str(REPO/'src'));from lean_agent.evaluator.tokens import without_comments
version=sys.argv[1];rows=[x for x in json.loads((HERE/'manifest.json').read_text())['problems'] if x['id'] in (8,9)]
pins=[next(v[version] for v in x['row']['version_info'] if version in v) for x in rows];assert len(set(pins))==1
S=REPO/'artifacts/live-practice'/('cslib-'+version);P=S/'project';S.mkdir(parents=True,exist_ok=True);logs=HERE/'setup-logs'/('cslib-'+version);logs.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,ELAN_HOME=str(S/'elan'),XDG_CACHE_HOME=str(S/'cache'));lake=str(Path.home()/'.elan/bin/lake')
def call(label,args,cwd=P):
 print('START',label,flush=True)
 with (logs/(label+'.log')).open('w') as f:r=subprocess.run(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 print('END',label,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(label)
if not P.exists():call('clone',['git','clone','--shared',str(REPO/'artifacts/live-practice/cslib-v4.33.0-rc2/project'),str(P)],REPO)
if subprocess.run(['git','cat-file','-e',pins[0]+'^{commit}'],cwd=P,capture_output=True).returncode:call('fetch',['git','fetch','--depth','1',rows[0]['row']['url'],pins[0]])
call('checkout',['git','checkout','--detach',pins[0]])
if not (S/'instructions-reviewed').exists():print('REVIEW_INSTRUCTIONS',P,flush=True);raise SystemExit(10)
for x in rows:
 f=P/x['row']['file_path']
 if not f.exists() or f.read_text().count(x['row']['src'])!=1:raise RuntimeError('Reference/context mismatch at '+str(x['id'])+' '+version)
call('toolchain',[str(Path.home()/'.elan/bin/elan'),'toolchain','install','leanprover/lean4:'+version])
todo=[x['row']['file_path'][:-5].replace('/','.') for x in rows];seen=set();cache=set()
while todo:
 mod=todo.pop()
 if mod in seen:continue
 seen.add(mod);f=P/(mod.replace('.','/')+'.lean')
 if not f.exists():
  if not mod.startswith(('Lean.','Init.','Std.')) and mod not in ('Lean','Init','Std'):cache.add(mod)
  continue
 for line in without_comments(f.read_text()).splitlines():
  q=re.match(r'^(?:public |private |meta )?import (?:all )?(.+)$',line)
  if q:todo.extend(q[1].split())
call('cache-targeted',[lake,'exe','cache','get',*sorted(cache)])
call('build-targeted',[lake,'build',*sorted({x['row']['file_path'][:-5].replace('/','.') for x in rows})])
(HERE/('cslib-'+version+'-compat-ready.json')).write_text(json.dumps({'project':str(P),'version':version,'pin':pins[0],'ids':[8,9]}))
