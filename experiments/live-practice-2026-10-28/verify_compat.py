"""Check the unchanged primary-selected proof in an extra pinned version.
No generation, repair or reselection occurs in this audit.
"""
import json,sys,re,hashlib
from pathlib import Path
from run import HERE,REPO,harness
from compat_evaluator import CompatibilityEvaluator
source=sys.argv[1];version=sys.argv[2];S=REPO/'artifacts/live-practice'/(source+'-'+version);P=S/'project'
items=[x for x in json.loads((HERE/'manifest.json').read_text())['problems'] if x['id'] in ((8,9) if source=='cslib' else (12,))]
for item in items:
 n=item['id'];row=item['row'];root=REPO/'runs/live-practice-2026-10-28'/str(n);out=root/'compatibility'/version
 if (out/'result.json').exists():print('EXISTS',n,version,flush=True);continue
 out.mkdir(parents=True,exist_ok=True)
 source=(P/row['file_path']).read_text();assert source.count(row['src'])==1
 lines=source.replace(row['src'],'{{DECLARATION}}').splitlines(True);imports=[i for i,l in enumerate(lines) if re.match(r'^(public |private |meta )?import ',l)]
 lines.insert(max(imports)+1,'{{HARNESS_COMMANDS}}\n');lines.insert(min(imports),'{{HARNESS_IMPORT}}\n');template=''.join(lines)
 problem=harness.read(root/'raw-v2/input/problem.json');selected=(root/'raw-v2/selected.lean').read_text();assert selected.startswith(problem['statement'])
 env={'id':'compat','project':str(P),'template':template,'toolchain':(P/'lean-toolchain').read_text().strip(),'command':[sys.executable,str(HERE/'lean_env.py'),str(S/'elan'),str(S/'cache'),'-j1'],'timeout_seconds':180}
 ev=CompatibilityEvaluator(P);fingerprint=ev.fingerprint(env)
 if (out/'input.json').exists():
  previous=harness.read(out/'input.json');assert previous['fingerprint']==fingerprint and previous['selected_sha256']==hashlib.sha256(selected.encode()).hexdigest(),'Changed audit input/environment'
 (out/'context.lean.in').write_text(template);(out/'selected.lean').write_text(selected);harness.write(out/'input.json',{'problem':problem,'environment':{k:v for k,v in env.items() if k!='template'},'fingerprint':fingerprint,'selected_sha256':hashlib.sha256(selected.encode()).hexdigest()})
 def evaluate(code,folder):
  if (folder/'result.json').exists():return harness.read(folder/'result.json')
  if folder.exists():
   i=1
   while folder.with_name(folder.name+f'-interrupted-{i}').exists():i+=1
   folder.rename(folder.with_name(folder.name+f'-interrupted-{i}'))
  result=ev.evaluate(code,problem,[env],folder,1);harness.write(folder/'result.json',result);return result
 baseline=evaluate(problem['reference'],out/'original')
 if baseline['valid']:
  ev.baseline_axioms={label:set().union(*(set(r['measurement']['axioms']) for r in result['runs'] if 'measurement' in r)) for label,result in baseline['environments'].items()}
  result=evaluate(selected,out/'selected') if selected!=problem['reference'] else baseline
 else:result=None
 assert fingerprint==ev.fingerprint(env),'Environment drift'
 record={'id':n,'version':version,'original_valid':baseline['valid'],'selected_valid':result['valid'] if result else None,'status':'pass' if result and result['valid'] else 'selected_rejected' if result else 'baseline_or_instrumentation_rejected','original':baseline,'selected':result,'selected_sha256':hashlib.sha256(selected.encode()).hexdigest()}
 harness.write(out/'result.json',record);print('COMPAT',n,version,record['status'],flush=True)
