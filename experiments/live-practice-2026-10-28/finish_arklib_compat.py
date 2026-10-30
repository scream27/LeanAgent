"""Sequential, resumable compatibility worker; raw audits and source checkouts survive cleanup."""
import subprocess,sys,json,shutil,datetime
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];root=R/'runs/live-practice-2026-10-28/12'
if not (root/'raw-v2/summary.json').exists():raise SystemExit('WAIT: primary selection is not final')
if not json.loads((root/'raw-v2/summary.json').read_text())['final_valid']:raise SystemExit('STOP: primary final verification failed')
for n,stage in [(15,'steps-002'),(19,'steps-002'),(19,'final')]:
 if not (R/f'runs/live-practice-2026-10-28/{n}/posthoc-timeout-retry/{stage}/result.json').exists():raise SystemExit('WAIT: timeout diagnostic is still running')
for version in ['v4.30.0','v4.29.0','v4.28.0']:
 result=root/'compatibility'/version/'result.json';S=R/'artifacts/live-practice'/('arklib-'+version)
 if not result.exists():
  for name,args in [('prepare',['prepare_arklib_compat.py',version]),('verify',['verify_compat.py','arklib',version])]:
   log=H/'setup-logs'/('arklib-'+version)/(name+'-compat-worker.log');log.parent.mkdir(parents=True,exist_ok=True)
   print('START',version,name,flush=True)
   with log.open('w') as f:p=subprocess.run([sys.executable,str(H/args[0]),*args[1:]],cwd=R,stdout=f,stderr=subprocess.STDOUT)
   print('END',version,name,p.returncode,flush=True)
   if p.returncode:raise SystemExit(p.returncode)
  assert result.exists()
 record=json.loads(result.read_text());print('RESULT',version,record['status'],flush=True)
 removed=[]
 for p in [S/'project/.lake',S/'elan',S/'cache']:
  if p.exists():
   assert p.is_dir() and not p.is_symlink();shutil.rmtree(p);removed.append(str(p))
 if removed:(H/('arklib-'+version+'-cleanup.json')).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deleted_generated_directories':removed,'audit':str(result.relative_to(R))},indent=2))
print('ALL_ARKLIB_COMPAT_ATTEMPTED',flush=True)
