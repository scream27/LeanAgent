import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];WORK=REPO.parent
SCRATCH=REPO/'artifacts/harness-expansion/physlib-v4.32.0';PROJECT=SCRATCH/'project'
PIN='c48433678e8fb6306ebcd48453300c8e16058a62'
def prepare():
 SCRATCH.mkdir(parents=True,exist_ok=True);logs=HERE/'setup_logs';logs.mkdir(exist_ok=True)
 env=dict(os.environ,ELAN_HOME=str(SCRATCH/'elan'),XDG_CACHE_HOME=str(SCRATCH/'cache'))
 def call(label,args,cwd):
  print('START',label,flush=True);start=time.monotonic()
  with (logs/(label+'.log')).open('w') as out:r=subprocess.run(args,cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT)
  print('END',label,r.returncode,round(time.monotonic()-start,1),flush=True)
  if r.returncode:raise RuntimeError(label+' failed')
 if not PROJECT.exists():call('clone',['git','clone','--shared',str(WORK/'refactor_arena/prompt_sweep_2026_10_15/environments/physlib'),str(PROJECT)],REPO)
 call('checkout',['git','checkout','--detach',PIN],PROJECT)
 call('toolchain',[str(Path.home()/'.elan/bin/elan'),'toolchain','install','leanprover/lean4:v4.32.0'],PROJECT)
 call('cache',[str(Path.home()/'.elan/bin/lake'),'exe','cache','get'],PROJECT)
 rows=[json.loads(l) for l in (WORK/'refactor_arena/benchmark_data_warmup.jsonl').read_text().splitlines()]
 call('build',[str(Path.home()/'.elan/bin/lake'),'build',*[rows[i-1]['file_path'][:-5].replace('/','.') for i in (4,5,6)]],PROJECT)
 (HERE/'environment-ready.json').write_text(json.dumps({'project':str(PROJECT),'pin':PIN,'toolchain':'leanprover/lean4:v4.32.0'},indent=2))
if __name__=='__main__':prepare()
