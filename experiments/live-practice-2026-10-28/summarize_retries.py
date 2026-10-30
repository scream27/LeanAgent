"""Summarize post-hoc verification retries separately from harness outcomes."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
def main():
 rows=[]
 for n,stage in [(15,'steps-002'),(19,'steps-002'),(19,'final')]:
  root=R/'runs/live-practice-2026-10-28'/str(n);p=root/'posthoc-timeout-retry'/stage/'result.json';row={'id':n,'stage':stage,'status':'pending','model_calls':0,'proof_edits':0}
  if p.exists():
   r=json.loads(p.read_text());s=json.loads((root/'raw-v2/summary.json').read_text());b=s['baseline'];inc=s['state']['best'];row.update(status='pass' if r['valid'] else 'rejected',result_path=str(p.relative_to(R)),error=r.get('error'),metrics=r.get('metrics'))
   if r['valid']:
    f=r['metrics'];score=lambda x:100*(3-x['tokens']/b['tokens']-x['raw_heartbeats']/b['raw_heartbeats'])/3
    row.update(local_final_score=score(f),harness_selection_score=score(inc),score_gain_over_harness_selection=score(f)-score(inc),proof_sha256=hashlib.sha256((p.parent/'candidate.lean').read_bytes()).hexdigest())
  rows.append(row)
 (H/'posthoc-retries.json').write_text(json.dumps({'protocol':'One unchanged-code retry of three fresh measurements; sealed primary outcomes are not overwritten.','rows':rows},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
