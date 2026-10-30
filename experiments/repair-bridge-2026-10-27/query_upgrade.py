"""Exploratory follow-up: positionless plain-text suggestions -> Lean JSON.
Triggered by the two observed successful queries whose suggestions lacked positions.
Frozen first pass is unchanged. No LLM is invoked.
"""
import json,re
from pathlib import Path
from bridge import HERE,REPO,PreparedEvaluator,harness
from local_pass import explicit_suggestion
from lean_agent.evaluator.lean import execute,render

def run():
 root=REPO/'runs/repair-bridge-2026-10-27/1';raw=root/'raw';out=root/'json-query-followup'
 out.mkdir(exist_ok=False)
 problem=harness.read(raw/'input/problem.json');config=harness.read(raw/'input/config.json');template=(raw/'input/context.lean.in').read_text()
 env={'id':'fixed','project':str(raw/'input/project'),'template':template,**{k:config['lean'][k] for k in ('toolchain','command','timeout_seconds')}}
 evaluator=PreparedEvaluator();base_result=harness.read(raw/'baseline/result.json');baseline=harness.metrics(base_result)
 evaluator.baseline_axioms={'fixed':set(base_result['environments']['fixed']['runs'][1]['measurement']['axioms'])}
 before=evaluator.fingerprint(env);harness.write(out/'environment.json',before)
 selected=harness.read(root/'local/summary.json')['after'];results=[]
 for attempt in (2,4):
  previous=root/'local'/f'step-3-attempt-{attempt}';source=(previous/'query.lean').read_text()
  sites=list(re.finditer(r'(?m)^\s*simp\? at (?:m|name)\s*$',source));assert len(sites)==1
  site=sites[0];token_start=source.index('simp?',site.start());line=source[:token_start].count('\n')+1
  d=out/f'attempt-{attempt}';d.mkdir();p=d/'query.lean';p.write_text(source)
  invocation=execute([*env['command'],'--json','--root='+str(d.resolve()),str(p.resolve())],evaluator.project,90)
  (d/'query.raw.jsonl').write_text(invocation['output']);harness.write(d/'invocation.json',invocation)
  messages=[]
  for l in invocation['output'].splitlines():
   try:messages.append(json.loads(l))
   except json.JSONDecodeError:pass
  messages=[m for m in messages if m.get('pos',{}).get('line')==line and 'Try this:' in m.get('data','')]
  suggestion=explicit_suggestion(messages[0]['data']) if len(messages)==1 else None
  item={'previous_attempt':str(previous.relative_to(REPO)),'expected_line':line,'matched_messages':messages,'suggestion':suggestion,'outcome':'no_supported_suggestion'}
  if suggestion:
   old=(raw/'steps/003/candidate.lean').read_text();variable='m' if attempt==2 else 'name'
   relative=token_start-source.index(problem['statement'])
   old_tactic='simp at '+variable
   assert old[relative:relative+len(old_tactic)]==old_tactic
   code=old[:relative]+suggestion+old[relative+len(old_tactic):]
   result=evaluator.evaluate(code,problem,[env],d/'explicit',3);harness.write(d/'explicit/result.json',result)
   item.update(outcome='valid' if result['valid'] else 'invalid',result=result)
   if result['valid']:
    c=harness.candidate(code,result,baseline);item['candidate']=c;item['beats_selected']=harness.ranking(c)<harness.ranking(selected)
    (d/'explicit-candidate.lean').write_text(code)
  results.append(item);print('JSON QUERY',attempt,suggestion,item['outcome'],flush=True)
 harness.write(out/'summary.json',{'results':results,'api_calls':0,'exploratory_followup':True,'environment_unchanged':evaluator.fingerprint(env)==before})
 (out/'query_upgrade.py').write_bytes(Path(__file__).read_bytes());harness.seal(out)
if __name__=='__main__':run()
