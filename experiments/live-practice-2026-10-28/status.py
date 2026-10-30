import json,html,datetime
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];M=json.loads((H/'manifest.json').read_text())
def read(p):return json.loads(p.read_text())
def main():
 rows=[]
 for item in M['problems']:
  n=item['id'];d=R/'runs/live-practice-2026-10-28'/str(n);raw=d/('raw-v2' if (d/'raw-v2').exists() else 'raw');status='not_started';steps=[]
  for event in sorted(raw.glob('steps/*/event.json')):
   s=read(event)['state_after'];steps.append({'step':s['step'],'valid':s['latest']['feedback']['valid'],'feedback':s['latest']['feedback']})
  if raw.exists():status='in_progress_or_interrupted'
  waiting=[str(p.relative_to(R)) for p in d.glob('exchange*/*/request.json') if not (p.parent/'reply.json').exists()]
  if waiting:status='waiting_for_conversation_model'
  summary=read(raw/'summary.json') if (raw/'summary.json').exists() else None
  if summary:status='complete' if summary['final_valid'] else 'final_verification_failed'
  error_path=d/('run-error-v2.json' if raw.name=='raw-v2' else 'run-error.json');error=read(error_path) if error_path.exists() else None
  if error:status='failed_before_completion'
  baseline_path=raw/'baseline/result.json'
  if baseline_path.exists() and not read(baseline_path)['valid']:
   status='baseline_rejected'
   if error is None:error={'type':'BaselineValidationFailure','details':read(baseline_path)}
  versions=[v for entry in item['row']['version_info'] for v in entry]
  checks={v:None for v in versions}
  if summary:checks[versions[0]]=summary['final_valid']
  for version in versions[1:]:
   cp=d/'compatibility'/version/'result.json'
   if cp.exists():checks[version]=read(cp)['selected_valid']
  compatibility={'checks':checks,'passed':sum(v is True for v in checks.values()),'required':len(checks),'all_measured':all(v is not None for v in checks.values())}
  rows.append({'id':n,'name':item['row']['name'],'members':item['members'],'status':status,'steps':steps,'pending':waiting,'error':error,'summary':summary,'compatibility':compatibility})
 out={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total_rows':35,'unique_problems':29,'api_calls':0,'rows':rows}
 (H/'progress.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('\n'.join(f"{x['id']:02} {x['status']} calls={len(x['steps'])} {x['name']}" for x in rows))
if __name__=='__main__':main()
