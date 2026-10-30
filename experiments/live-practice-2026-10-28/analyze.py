"""Export auditable selections, failures and provisional primary-version scores."""
import json
from pathlib import Path
from status import main as update
H=Path(__file__).resolve().parent;R=H.parents[1]
def main():
 update();p=json.loads((H/'progress.json').read_text());m=json.loads((H/'manifest.json').read_text());out=[]
 for item,row in zip(m['problems'],p['rows']):
  n=row['id'];root=R/'runs/live-practice-2026-10-28'/str(n);raw=root/('raw-v2' if (root/'raw-v2').exists() else 'raw')
  record={k:row[k] for k in ('id','name','members','status')};record['failure']=row['error'];record['compatibility']=row['compatibility'];record['attempts']=row['steps'];record['versions_requested']=item['row']['version_info']
  s=row['summary']
  if s and s['final_valid']:
   problem=json.loads((raw/'input/problem.json').read_text());b=s['baseline'];f=s['final'];code=s['state']['best']['code']
   token_gain=1-f['tokens']/b['tokens'];hb_gain=1-f['raw_heartbeats']/b['raw_heartbeats']
   record.update(baseline=b,final=f,selected_code=code,proof=code[len(problem['statement']):].split(':=',1)[1].strip(),original_fallback=code.strip()==problem['reference'].strip(),raw_original_identical=code==problem['reference'],primary_common_cost=(2-token_gain-hb_gain)/2,primary_only_score=100*(token_gain+hb_gain+1)/3,score_note='Primary-version proxy only; robustness across requested versions is not inferred.',final_sample_range=[min(f['raw_samples']),max(f['raw_samples'])])
   if record['compatibility']['all_measured']:
    robustness=record['compatibility']['passed']/record['compatibility']['required'];record['local_final_score']=100*(token_gain+hb_gain+robustness)/3
   record['outcome']='original_fallback' if record['original_fallback'] else 'improved_primary' if token_gain+hb_gain>0 else 'not_improved_primary'
  out.append(record)
 per_row=[]
 for item,record in zip(m['problems'],out):
  for member in item['members']:
   per_row.append({**member,'unique_problem_id':record['id'],'name':record['name'],'status':record['status'],'proof':record.get('selected_code',item['row']['src']),'verified_primary':record['status']=='complete','original_retained_without_validation':record['status']!='complete','score_primary_proxy':record.get('primary_only_score'),'score_final_local':record.get('local_final_score'),'compatibility':record['compatibility'],'note':'Uncompleted or rejected originals are retained for inspection, not certified submissions.'})
 (H/'per-dataset-results.json').write_text(json.dumps(per_row,ensure_ascii=False,indent=2)+'\n')
 (H/'selections.json').write_text(json.dumps({'official_evaluation':False,'all_primary_attempts_finished':all(x['status'] in ('complete','baseline_rejected','final_verification_failed') for x in out),'all_runs_successfully_completed':all(x['status']=='complete' for x in out),'unique_problems':out,'total_dataset_rows':35,'api_calls':0,'conversation_usage':'unmeasured'},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
