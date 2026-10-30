"""Deterministically rank verified retry outputs; never overwrite primary harness results."""
import sys,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R/'src'))
from lean_agent import harness
rows=[]
for n in [15,19]:
 root=R/'runs/live-practice-2026-10-28'/str(n);raw=root/'raw-v2';problem=harness.read(raw/'input/problem.json');base=harness.read(raw/'baseline/result.json');summary=harness.read(raw/'summary.json');b=harness.metrics(base)
 pool=[('original',harness.candidate(problem['reference'],base,b))]
 if summary['final_valid']:pool.append(('primary_final',harness.candidate((raw/'selected.lean').read_text(),harness.read(raw/'final/result.json'),b)))
 for p in sorted((root/'posthoc-timeout-retry').glob('*/result.json')):
  result=harness.read(p)
  if result['valid']:pool.append((str(p.parent.relative_to(root)),harness.candidate((p.parent/'candidate.lean').read_text(),result,b)))
 name,best=min(pool,key=lambda x:harness.ranking(x[1]));score=lambda v:100*(3-v['tokens']/b['tokens']-v['raw_heartbeats']/b['raw_heartbeats'])/3
 rows.append({'id':n,'name':problem['name'],'source':name,'proof':best['code'],'sha256':best['sha256'],'tokens':best['tokens'],'raw_heartbeats':best['raw_heartbeats'],'local_final_score':score(best),'primary_harness_selection_score':score(summary['state']['best']),'gain_over_primary_selection':score(best)-score(summary['state']['best']),'primary_final_valid':summary['final_valid'],'original_fallback':best['code'].strip()==problem['reference'].strip(),'verified_pool':[{'source':label,'sha256':v['sha256'],'score':score(v)} for label,v in pool]})
(H/'retry-selected-proofs.json').write_text(json.dumps({'posthoc':True,'selection':harness.SELECTION,'additional_model_calls':0,'proof_edits':0,'scope':'Single-version P15 and P19 only; original is retained as fallback. Sealed primary runs are unchanged.','rows':rows},ensure_ascii=False,indent=2)+'\n')
print('\n'.join(f"P{x['id']} {x['source']}: {x['local_final_score']:.3f}" for x in rows))
