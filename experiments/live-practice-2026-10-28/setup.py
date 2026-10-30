import json,hashlib,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];ROOT=REPO.parent
DATA=ROOT/'LeanAgent/docs/research/verifier-guided-agent/validation-mini'
FILES=['arena_practice_benchmark.jsonl','lean_refactor_eval_analysis_warmup_format.jsonl','strata_local_practice_warmup_format.jsonl']
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def manifest():
 seen={};rows=[]
 for f in FILES:
  for i,line in enumerate((DATA/f).read_text().splitlines(),1):
   r=json.loads(line);key=json.dumps({k:r[k] for k in ['name','statement','src','url','file_path','version_info']},sort_keys=True,ensure_ascii=False)
   if key not in seen:
    seen[key]=len(rows)+1;rows.append({'id':len(rows)+1,'row':r,'members':[]})
   rows[seen[key]-1]['members'].append({'dataset':f,'row':i})
 write(HERE/'manifest.json',{'dataset_sha256':{f:hashlib.sha256((DATA/f).read_bytes()).hexdigest() for f in FILES},'unique_problems':len(rows),'total_rows':sum(len(x['members']) for x in rows),'problems':rows,'max_calls':3,'model':'current conversation model; external relay; no paid API calls','scope':'All rows attempted; environment/original failures remain distinct from model or harness failures.'})
 return rows

def prepare_input(item,project,command,source_root=None):
 n=item['id'];r=item['row'];d=HERE/'inputs'/str(n);d.mkdir(parents=True,exist_ok=True)
 source=((source_root or project)/r['file_path']).read_text()
 if source.count(r['src'])!=1:raise ValueError('Reference does not match pinned source exactly: '+str(n))
 template=source.replace(r['src'],'{{DECLARATION}}');lines=template.splitlines(True)
 imports=[i for i,l in enumerate(lines) if re.match(r'^(public |private |meta )?import ',l)]
 if not imports:raise ValueError('No imports in '+str(n))
 lines.insert(max(imports)+1,'{{HARNESS_COMMANDS}}\n');lines.insert(min(imports),'{{HARNESS_IMPORT}}\n')
 (d/'context.lean.in').write_text(''.join(lines));write(d/'problem.json',{'id':str(n),'name':r['name'],'statement':r['statement'],'reference':r['src']})
 (d/'prompt.txt').write_text((REPO/'examples/first-harness/prompt.txt').read_text())
 stub=d/'project';stub.mkdir(exist_ok=True);pin=(project/'lean-toolchain').read_text();(stub/'lean-toolchain').write_text(pin)
 write(d/'environment.json',{'project':str(project),'command':command,'version_info':r['version_info']})
 write(d/'config.json',{'schema_version':1,'problem':'problem.json','template':'context.lean.in','project':'project','prompt':'prompt.txt','lean':{'toolchain':pin.strip(),'command':command,'timeout_seconds':None,'repetitions':3},'limits':{'max_calls':3,'max_proof_characters':50000,'max_feedback_characters':14000,'max_request_characters':160000},'model':{'backend':'external','id':'current-conversation-model','exchange_directory':str(REPO/'runs/live-practice-2026-10-28'/str(n)/'exchange'),'timeout_seconds':43200,'max_tokens':20000}})

if __name__=='__main__':
 rows=manifest()
 for item in rows:
  r=item['row'];v=next(iter(r['version_info'][0]))
  if r['source']=='strata' and v=='v4.26.0':prepare_input(item,REPO/'artifacts/repair-bridge/strata',[str(Path.home()/'.elan/bin/lake'),'env','lean','-j1'])
  elif r['source']=='physlib':prepare_input(item,REPO/'artifacts/harness-expansion/physlib-v4.32.0/project',[sys.executable,str(REPO/'experiments/harness-expansion-2026-10-27/lean_command.py'),'-j1'])
 print('Manifest and prepared-environment inputs created')
