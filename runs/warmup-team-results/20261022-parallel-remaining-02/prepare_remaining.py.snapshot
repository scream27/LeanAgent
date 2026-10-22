"""Assemble local dependency overlays and build missing source modules in central cache.

Uses exact Git object revisions and existing compiled third-party dependencies;
never changes source checkouts or substitutes toolchains. No network or package
installation. A module cap prevents unintentionally rebuilding whole libraries.
"""
from pathlib import Path
import argparse,json,os,re,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[2]

def main():
 p=argparse.ArgumentParser();p.add_argument('--environments',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--max-modules',type=int,default=40)
 p.add_argument('--supplement', type=Path, default=Path(os.environ['PROJECT_CACHE_DIR']).parent/'LeanAgent/warmup15-xhigh/4.32.0/merged')
 args=p.parse_args(); mapping=json.loads(args.environments.read_text()); report=[]
 cases=[('physlib','Physlib','v4.32.0','c48433678e8fb6306ebcd48453300c8e16058a62',['Physlib.Electromagnetism.Dynamics.Lagrangian']),('cslib','Cslib','v4.32.0','197a7be621263b84c67ca4f803f69205b36d06df',['Cslib.Languages.CombinatoryLogic.Defs','Cslib.Foundations.Relation.Confluence','Cslib.Foundations.Semantics.LTS.Bisimulation','Cslib.Foundations.Syntax.Congruence','Cslib.Languages.CCS.Semantics'])]
 for source,namespace,version,rev,modules in cases:
  key=f'{version}@{rev}';e=mapping[key]
  dest=Path(os.environ['PROJECT_CACHE_DIR'])/'warmup-team-results'/'remaining-dependencies'/source/rev
  src=dest/'src';lib=dest/'lib';logs=dest/'logs';logs.mkdir(parents=True,exist_ok=True);lib.mkdir(parents=True,exist_ok=True)
  # Lean resolves a namespace from its first directory; unify partial roots
  # rather than expecting per-file fallback across LEAN_PATH entries.
  roots=[Path(x) for x in e['libraryPaths']]
  roots.append(args.supplement)
  for root in roots:
   for path in root.rglob('*'):
    if not path.is_file() or not any(str(path).endswith(ext) for ext in ['.olean','.olean.private','.olean.server','.ilean','.ir']):continue
    link=lib/path.relative_to(root)
    if link.exists():continue
    link.parent.mkdir(parents=True,exist_ok=True);link.symlink_to(path.resolve())
  paths=[str(lib)]; count=0;visited=set()
  def build(module):
   nonlocal count
   rel=Path(*module.split('.'))
   for root in paths:
    compiled=Path(root)/rel.with_suffix('.olean')
    if compiled.is_file():
     report.append({'module':module,'status':'reused','path':str(compiled.resolve()),'sha256':hashlib.sha256(compiled.read_bytes()).hexdigest(),'sourceRevision':rev})
     return
   if module in visited:raise ValueError('dependency cycle '+module)
   if module.split('.')[0]!=namespace:raise ValueError('missing external dependency '+module)
   visited.add(module); count+=1
   if count>args.max_modules:raise ValueError(f'local build cap {args.max_modules} exceeded at {module}')
   code=subprocess.check_output(['git','-C',str(ROOT/'sources'/source),'show',f'{rev}:{rel}.lean'],text=True)
   for dependency in re.findall(r'(?m)^(?:(?:public|private|meta) )*import\s+([\w.]+)',code):build(dependency)
   path=src/rel.with_suffix('.lean');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(code)
   output=lib/rel.with_suffix('.olean');output.parent.mkdir(parents=True,exist_ok=True)
   command=[e['binary'],'-j1','-M2048','-o',str(output),str(path)]
   print('Building',module,flush=True)
   run=subprocess.run(command,cwd=src,env={**os.environ,'LEAN_PATH':':'.join(paths)},capture_output=True,text=True,timeout=120)
   (logs/(module+'.log')).write_text(run.stdout+run.stderr)
   report.append({'module':module,'sourceRevision':rev,'sourceSha256':hashlib.sha256(code.encode()).hexdigest(),'command':command,'returncode':run.returncode})
   if run.returncode:raise ValueError('compile failed '+module+': '+(run.stdout+run.stderr)[:500])
  for module in modules:
   try:build(module)
   except (ValueError,subprocess.SubprocessError) as error:report.append({'module':module,'error':str(error)});print(error,flush=True)
  e['libraryPaths']=paths
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
 args.output.with_name('preparation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
