"""Durable orchestration adapter; all proof parsing, feedback, ranking and replay
use the common harness functions. Never wait in a process for model input."""
import json,sys,hashlib,shutil,datetime
from pathlib import Path
from run import HERE,REPO,harness,LiveEvaluator
from run_v2 import V2Evaluator
from lean_agent import models

def preserve_partial(path):
 if path.exists():
  i=1
  while path.with_name(path.name+f'-interrupted-{i}').exists():i+=1
  path.rename(path.with_name(path.name+f'-interrupted-{i}'))

def resume(n):
 root=REPO/'runs/live-practice-2026-10-28'/str(n);d=HERE/'inputs'/str(n)
 v2=(root/'raw-v2').exists() or not (root/'raw').exists()
 output=root/('raw-v2' if v2 else 'raw');config_path=d/('config-v2.json' if v2 else 'config.json')
 if not config_path.exists():
  cfg=harness.read(d/'config.json');cfg['model']['exchange_directory']=str(root/'exchange-v2');harness.write(config_path,cfg)
 if (output/'summary.json').exists():
  print('COMPLETE',n,flush=True);return
 if not output.exists():
  config,paths=harness.load_config(config_path);manifest=harness.snapshot(output,config_path,paths)
 else:
  manifest=harness.read(output/'manifest.json') if (output/'manifest.json').exists() else None
  if manifest is None:raise RuntimeError('Interrupted before manifest: preserve and start a new run')
 config=harness.read(output/'input/config.json');problem=harness.read(output/'input/problem.json');prompt=(output/'input/prompt.txt').read_text()
 env={'id':'fixed','project':str(output/'input/project'),'template':(output/'input/context.lean.in').read_text(),**{k:config['lean'][k] for k in ('toolchain','command','timeout_seconds')}}
 project=Path(harness.read(d/'environment.json')['project']);ev=(V2Evaluator if v2 else LiveEvaluator)(project)
 fingerprint=ev.fingerprint(env)
 if (output/'manifest.json').exists():
  if fingerprint!=manifest['environment']:raise RuntimeError('Environment drift on resume')
 else:
  manifest['environment']=fingerprint;harness.write(output/'manifest.json',manifest)
 # Record adapter separately; original input/code snapshots remain untouched.
 adapter=output/'resume-adapter.py'
 if not adapter.exists():adapter.write_bytes(Path(__file__).read_bytes())
 elif adapter.read_bytes()!=Path(__file__).read_bytes():raise RuntimeError('Resume adapter changed')
 def evaluate(code,folder):
  if (folder/'result.json').exists():return harness.read(folder/'result.json')
  preserve_partial(folder)
  result=ev.evaluate(code,problem,[env],folder,config['lean']['repetitions']);harness.write(folder/'result.json',result);return result
 baseline_result=evaluate(problem['reference'],output/'baseline')
 state=harness.initial_state(problem,baseline_result);baseline=harness.metrics(baseline_result)
 ev.baseline_axioms={label:set().union(*(set(r['measurement']['axioms']) for r in row['runs'] if 'measurement' in r)) for label,row in baseline_result['environments'].items()}
 if not (output/'initial-state.json').exists():harness.write(output/'initial-state.json',state)
 stop='call_limit'
 for step in range(1,config['limits']['max_calls']+1):
  folder=output/'steps'/f'{step:03}'
  if (folder/'event.json').exists():
   state=harness.read(folder/'event.json')['state_after'];continue
  try:body=harness.make_request(state,problem,config,prompt)
  except ValueError:stop='context_limit';break
  request=folder/'request.json'
  if request.exists():
   if harness.read(request)!=body:raise RuntimeError('Saved request differs from resumed state')
  else:harness.write(request,body)
  response=folder/'response.json'
  if response.exists():raw=harness.read(response)
  else:
   exchange=Path(config['model']['exchange_directory'])/f'{step:03}';exchange.mkdir(parents=True,exist_ok=True)
   digest=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
   packet={'request_sha256':digest,'request':body};pending=exchange/'request.json'
   if pending.exists():
    if harness.read(pending)!=packet:raise RuntimeError('Exchange request differs')
   else:harness.write(pending,packet)
   if not (exchange/'reply.json').exists():
    print('AWAITING_MODEL',n,step,str(pending),flush=True);return
   reply=harness.read(exchange/'reply.json')
   if reply['request_sha256']!=digest:raise RuntimeError('Stale model response')
   raw={'id':f'external-{digest}','model':config['model']['id'],'provider':'conversation-relay','choices':[{'message':{'role':'assistant','content':reply.get('content')}}],'usage':{'cost':0},'external_request_sha256':digest,'cost_note':'No API charged by this harness; conversation token usage is unmeasured.'}
   harness.write(response,raw)
  code=result=rejection=None
  try:code=harness.parse_proof(raw,problem,config['limits']['max_proof_characters'])
  except (ValueError,TypeError) as e:rejection=str(e)
  if code is not None:
   candidate=folder/'candidate.lean'
   if candidate.exists() and candidate.read_text()!=code:raise RuntimeError('Candidate drift')
   candidate.write_text(code);result=evaluate(code,folder/'evaluation')
  state=harness.advance(state,raw,code,result,rejection,baseline,config,str(output));harness.write(folder/'event.json',{'state_after':state,'rejection':rejection})
  if state['unknown_cost']:stop='unknown_cost';break
  if result and harness.environment_failed(result):stop='environment_failed';break
 (output/'selected.lean').write_text(state['best']['code']);final=evaluate(state['best']['code'],output/'final')
 if ev.fingerprint(env)!=manifest['environment']:raise RuntimeError('Environment changed')
 summary=harness.summarize(state,baseline,final,config,stop);harness.write(output/'summary.json',summary);harness.seal(output)
 harness.write(root/('replay-resumed-v2.json' if v2 else 'replay-resumed.json'),harness.replay(output))
 print('COMPLETE',n,summary['final_valid'],flush=True)
if __name__=='__main__':
 for n in map(int,sys.argv[1:]):resume(n)
