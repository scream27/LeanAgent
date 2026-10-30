"""Prepare one new primary-version group; never reuse a user's checkout."""
import os,sys,json,subprocess
from pathlib import Path
from setup import HERE,REPO,ROOT,prepare_input
source=sys.argv[1];rows=[x for x in json.loads((HERE/'manifest.json').read_text())['problems'] if x['row']['source']==source]
version=sys.argv[2] if len(sys.argv)>2 else next(iter(rows[0]['row']['version_info'][0]))
rows=[x for x in rows if version in x['row']['version_info'][0]]
if not rows:raise RuntimeError('No primary problems for group')
pin=rows[0]['row']['version_info'][0][version];assert all(x['row']['version_info'][0][version]==pin for x in rows)
S=REPO/'artifacts/live-practice'/f'{source}-{version}';P=S/'project';S.mkdir(parents=True,exist_ok=True)
logs=HERE/'setup-logs'/f'{source}-{version}';logs.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,ELAN_HOME=str(S/'elan'),XDG_CACHE_HOME=str(S/'cache'))
def call(label,args,cwd=P):
 print('START',label,flush=True)
 with (logs/(label+'.log')).open('w') as f:r=subprocess.run(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 print('END',label,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(label)
old=ROOT/'refactor_arena/prompt_sweep_2026_10_15/environments'/source
if not P.exists():
 args=['git','clone','--shared',str(old),str(P)] if old.exists() else ['git','clone','--filter=blob:none','--no-checkout',rows[0]['row']['url'],str(P)]
 call('clone',args,REPO)
if subprocess.run(['git','cat-file','-e',pin+'^{commit}'],cwd=P,capture_output=True).returncode:call('fetch',['git','fetch','--depth','1',rows[0]['row']['url'],pin])
call('checkout',['git','checkout','--detach',pin])
# Stop before building on unexpected repo instructions; the orchestrator reads them.
if not (S/'instructions-reviewed').exists():
 print('REVIEW_INSTRUCTIONS',P,flush=True);raise SystemExit(10)
call('toolchain',[str(Path.home()/'.elan/bin/elan'),'toolchain','install','leanprover/lean4:'+version])
if '--toolchain-only' in sys.argv:raise SystemExit(0)
if source!='strata':
 cache_targets=[x for x in json.loads((HERE/'cslib-external-imports.json').read_text()) if not x.startswith('Lean.')] if source=='cslib' else []
 call('cache',[str(Path.home()/'.elan/bin/lake'),'exe','cache','get',*cache_targets])
call('build',[str(Path.home()/'.elan/bin/lake'),'build',*sorted({x['row']['file_path'][:-5].replace('/','.') for x in rows})])
for x in rows:prepare_input(x,P,[sys.executable,str(HERE/'lean_env.py'),str(S/'elan'),str(S/'cache'),'-j1'])
(HERE/f'{source}-{version}-ready.json').write_text(json.dumps({'project':str(P),'ids':[x['id'] for x in rows]}))
