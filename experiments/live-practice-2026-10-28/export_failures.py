"""Export actual failed candidates as repair-agent inputs without fabricating errors."""
import json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
def read(p):return json.loads(p.read_text())
def main():
 cases=[]
 for folder in sorted((R/'runs/live-practice-2026-10-28').iterdir(),key=lambda p:int(p.name)):
  raw=folder/('raw-v2' if (folder/'raw-v2').exists() else 'raw');problem_path=raw/'input/problem.json'
  if not problem_path.exists():continue
  problem=read(problem_path)
  for path in sorted(raw.glob('steps/*/event.json')):
   step=path.parent;event=read(path);latest=event['state_after']['latest']
   if latest['feedback']['valid']:continue
   code=latest['code'];logs=[]
   for log in step.glob('evaluation/*/*.log'):
    logs.append({'path':str(log.relative_to(R)),'content':log.read_text()})
   # Feedback is exactly what the conversation model received; full logs remain available.
   cases.append({'case_id':f"practice-{folder.name}-step-{step.name}",'problem_id':int(folder.name),'name':problem['name'],'statement':problem['statement'],'original':problem['reference'],'failed_candidate':code,'feedback':latest['feedback'],'logs':logs,'context_template':str((raw/'input/context.lean.in').relative_to(R)),'environment_manifest':str((raw/'manifest.json').relative_to(R)),'repair_constraint':'Only replace proof body; preserve statement, imports and context. Verify with pinned Lean and reject sorry/new axioms.','incumbent_after_failure':event['state_after']['best']['code']})
 (H/'repair-cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases))
 print('Exported',len(cases),'observed failed candidate cases')
if __name__=='__main__':main()
