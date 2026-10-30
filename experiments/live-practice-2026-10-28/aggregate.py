"""Keep primary outcomes and posthoc selections separate; never impute blocked scores."""
import json, statistics, collections
from pathlib import Path
H=Path(__file__).resolve().parent
rows=json.loads((H/'selections.json').read_text())['unique_problems']
retries=json.loads((H/'retry-selected-proofs.json').read_text())['rows']
valid=[r for r in rows if r['status']=='complete']
scored=[r for r in valid if 'local_final_score' in r]
out={'scope':'29 unique problems / 35 dataset rows; no official leaderboard evaluation',
 'primary_status_counts':dict(collections.Counter(r['status'] for r in rows)),
 'primary_outcome_counts':dict(collections.Counter(r.get('outcome','not_scored') for r in rows)),
 'model_responses':sum(len(r['attempts']) for r in rows),
 'rejected_responses':sum(not a['valid'] for r in rows for a in r['attempts']),
 'primary_verified_subset':{'n':len(valid),'mean_primary_proxy':statistics.mean(r['primary_only_score'] for r in valid),'original_reference_score':100/3},
 'fully_measured_subset':{'n':len(scored),'mean_local_final_score':statistics.mean(r['local_final_score'] for r in scored) if scored else None},
 'unmeasured_scores_are_not_zero':True,
 'posthoc_recovered_selection_ids':[r['id'] for r in retries],
 'posthoc_additional_model_calls':0,
 'note':'Subset means exclude baseline rejection and failed final verification. They are not whole-dataset performance. Original fallback micro-differences are measurement noise.'}
retry_by_id={r['id']:r for r in retries}
if len(scored)==len(valid):
 after=[retry_by_id[r['id']]['local_final_score'] if r['id'] in retry_by_id else r['local_final_score'] for r in scored]
 recovered=[r for r in retries if r['id'] not in {x['id'] for x in scored}]
 out['posthoc_comparison']={'fixed_cohort_n':len(scored),'before_mean':statistics.mean(r['local_final_score'] for r in scored),'after_mean':statistics.mean(after),'newly_verified_ids':[r['id'] for r in recovered],'expanded_cohort_n':len(after)+len(recovered),'expanded_mean':statistics.mean(after+[r['local_final_score'] for r in recovered]),'warning':'Expanded mean has a different denominator; do not attribute its change solely to score improvement.'}
(H/'aggregate.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
