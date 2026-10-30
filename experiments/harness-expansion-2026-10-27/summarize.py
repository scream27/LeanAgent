"""Aggregate sealed runs; do not infer success from a generated candidate."""
import json,sys,difflib,html,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'src'))
from lean_agent.harness import metrics,replay

def read(p):return json.loads(p.read_text())
def axes(m,b):
 l=100*(1-m['tokens']/b['tokens']);h=100*(1-m['raw_heartbeats']/b['raw_heartbeats'])
 return {'length_reduction':l,'heartbeat_reduction':h,'robustness':100.,'score':(l+h+100)/3}
def main():
 rows=[];export=[]
 for n in (4,5,6):
  base=REPO/'runs/harness-expansion-2026-10-27'/str(n)/'raw-v2';s=read(base/'summary.json');p=read(base/'input/problem.json')
  verified=replay(base)
  b=s['baseline'];steps=[];labels=read(HERE/'inputs'/str(n)/'strategies.json')
  for i,label in enumerate(labels,1):
   d=base/'steps'/f'{i:03}';r=read(d/'evaluation/result.json');m=metrics(r)
   code=(d/'candidate.lean').read_text()
   diagnostics=[]
   for env in r['environments'].values():
    if env.get('error'):
     error=dict(env['error'])
     failed=next((z for z in env['runs'] if z['returncode'] or z['timed_out']),None)
     if failed:
      logpath=d/'evaluation/fixed'/failed['log'];log=logpath.read_text()
      error['full_log']=str(logpath.relative_to(REPO))
      error['first_error']=next((line for line in log.splitlines() if 'error:' in line),None)
     diagnostics.append(error)
   steps.append({'candidate':i,'strategy':label,'valid':r['valid'],'metrics':m,'axes':axes(m,b) if m else None,'diagnostics':diagnostics,'proof':code,'diff':''.join(difflib.unified_diff(p['reference'].splitlines(True),code.splitlines(True),fromfile='original',tofile='candidate'))})
  selected=s['state']['best'];final=s['final'];assert s['final_valid']
  selected_i=next((x['candidate'] for x in steps if x['proof']==selected['code']),None)
  row={'id':n,'name':p['name'],'baseline':b,'candidates':steps,'selected_candidate':selected_i,'selected':selected,'final':final,'final_axes':axes(final,b),'final_valid':s['final_valid'],'fallback':selected['code']==p['reference'],'replay':verified,'raw_run':str(base.relative_to(REPO)),'versions':p['version_info']}
  rows.append(row);export.append({'name':p['name'],'proof':selected['code']})
 previous=read(REPO/'experiments/repair-bridge-2026-10-27/refactoring_results.json')
 old=read(REPO.parent/'LeanAgent/docs/research/verifier-guided-agent/experiments/local-minimizer-2026-10-21/results.json')
 prior=[]
 for p in previous['problems']:
  # Use the common harness final revalidation, not a post-local repair proposal.
  raw=read(REPO/'runs/repair-bridge-2026-10-27'/str(p['id'])/'raw/summary.json')
  prior.append({'id':p['id'],'axes':axes(raw['final'],raw['baseline'])})
 scores=[p['axes']['score'] for p in prior]+[p['final_axes']['score'] for p in rows]
 replaced={p['id']:p['axes']['score'] for p in prior}|{p['id']:p['final_axes']['score'] for p in rows}
 compare={'prior_p1_p2_common_harness':prior,'measured_five_mean':statistics.mean(scores),'previous_fifteen_mean':statistics.mean(p['final_score'] for p in old),'mixed_fifteen_projection':statistics.mean(replaced.get(p['id'],p['final_score']) for p in old),'fixed_five_remaining_perfect_upper_bound':(sum(scores)+10*100)/15,'warning':'Five-problem mean is not a leaderboard score; mixed projection reuses historical measurements and is not a new 15-problem evaluation.'}
 result={'schema_version':1,'official_evaluation':False,'api_calls':0,'generation':'Conversation-authored fixed fixtures, three candidates per problem; no live model inference or claim of harness autonomous generation.','problems':rows,'comparison':compare,'leaderboard':read(HERE/'leaderboard/rows.json'),'leaderboard_provenance':read(HERE/'leaderboard/provenance.json')}
 (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 (HERE/'arena-submission.json').write_text(json.dumps(export,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'summary':[{k:p[k] for k in ('id','selected_candidate','final_axes')} for p in rows],'comparison':compare},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
