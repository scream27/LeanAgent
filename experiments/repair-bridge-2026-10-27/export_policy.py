"""Feed actual unresolved observations into the unchanged existing repair policy."""
import importlib.util, shutil
from pathlib import Path
from bridge import HERE,REPO,harness
from lean_agent.evaluator.tokens import proof_body
from lean_agent.evaluator.lean import render,sha256
POLICY_SOURCE=REPO.parent/'LeanAgent/docs/research/verifier-guided-agent/escalation_policy.py'
def export():
 dest=HERE/'escalation_policy.py'
 if not dest.exists():shutil.copyfile(POLICY_SOURCE,dest)
 spec=importlib.util.spec_from_file_location('frozen_repair_policy',dest);policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
 for n in (1,2):
  root=REPO/'runs/repair-bridge-2026-10-27'/str(n);raw=root/'raw';local=harness.read(root/'local/summary.json')
  problem=harness.read(raw/'input/problem.json');template=(raw/'input/context.lean.in').read_text();original=proof_body(problem['reference'],problem['statement'])
  original_source=render(template,problem['reference'],problem['name'],None)
  start=original_source.index(problem['reference'])+len(problem['reference'])-len(original)
  for step in range(1,4):
   folder=raw/'steps'/f'{step:03}';result=harness.read(folder/'evaluation/result.json')
   if result['valid']:continue
   attempts=[a for a in local['attempts'] if a['source_step']==step]
   if any(a['outcome']=='valid' for a in attempts):continue
   code=(folder/'candidate.lean').read_text();body=proof_body(code,problem['statement'])
   request={'problem_id':problem['name'],'status':'invalid','baseline_verified':True,'preview_only':True,'environment':problem['version_info'],'environment_hash':harness.read(root/'local/environment.json')['prepared_closure']['sha256'],'statement':problem['statement'],'context':{'template_file':str(raw/'input/context.lean.in'),'note':'Full frozen source is in the attached file; not reproduced in this preview. No trusted pre-error state was collected.'},'original_proof':original,'candidate_proof':body,'candidate_hash':sha256(body),'source_contract':{'original_source':original_source,'candidate_source':render(template,code,problem['name'],None),'body_start':start,'body_end':start+len(original)},'diagnostics':(folder/'evaluation/fixed/check.log').read_text(),'localization':{'scope':'body'},'local':{'state':'exhausted','evidence':[{'operator':a['operator'],'outcome':a['outcome'],'log':a['log']} for a in attempts]},'incumbent':local['after'],'llm_history':[],'constraints':['Only proof body may change','No sorry, new axioms, target self-reference','Adapter must convert candidate/proof_body response to common harness proof field before parse_proof; need_context/no_candidate are control signals']}
   out=root/'escalation'/f'{step:03}';decision=policy.decide(request)
   harness.write(out/'request.json',request);harness.write(out/'decision.json',decision)
   if decision['prompt']:(out/'prompt.txt').write_text(decision['prompt'])
if __name__=='__main__':export()
