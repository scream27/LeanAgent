"""One post-hoc deterministic retry per observed timeout; sealed runs stay untouched.
Run only after competing environment builds finish. No proof edits or model calls.
"""
import sys,json
from pathlib import Path
from run import HERE,REPO,harness
from run_v2 import V2Evaluator
for n,rel in [(15,'steps/002'),(19,'steps/002'),(19,'final')]:
 root=REPO/'runs/live-practice-2026-10-28'/str(n);raw=root/'raw-v2';original_folder=raw/rel/('evaluation' if rel.startswith('steps') else '')
 original=harness.read(original_folder/'result.json')
 if not any(x.get('error',{}).get('kind')=='timeout' for x in original['environments'].values() if x.get('error')):continue
 out=root/'posthoc-timeout-retry'/rel.replace('/','-')
 if (out/'result.json').exists():print('EXISTS',n,rel,flush=True);continue
 out.mkdir(parents=True,exist_ok=True)
 problem=harness.read(raw/'input/problem.json');config=harness.read(raw/'input/config.json');project=Path(harness.read(HERE/'inputs'/str(n)/'environment.json')['project'])
 env={'id':'fixed','project':str(project),'template':(raw/'input/context.lean.in').read_text(),**{k:config['lean'][k] for k in ('toolchain','command','timeout_seconds')}}
 ev=V2Evaluator(project);fingerprint=ev.fingerprint(env);assert fingerprint==harness.read(raw/'manifest.json')['environment']
 baseline=harness.read(raw/'baseline/result.json');ev.baseline_axioms={label:set().union(*(set(r['measurement']['axioms']) for r in row['runs'] if 'measurement' in r)) for label,row in baseline['environments'].items()}
 code=(raw/rel/'candidate.lean').read_text() if rel.startswith('steps') else (raw/'selected.lean').read_text()
 (out/'candidate.lean').write_text(code);harness.write(out/'protocol.json',{'posthoc':True,'model_calls':0,'proof_edits':0,'maximum_retries':1,'original_timeout_seconds':env['timeout_seconds'],'repetitions':3,'fingerprint':fingerprint,'original_result':str((original_folder/'result.json').relative_to(REPO))})
 evaluation=out/'evaluation'
 if evaluation.exists():
  print('INTERRUPTED_RETRY_REQUIRES_REVIEW',n,rel,flush=True);continue
 result=ev.evaluate(code,problem,[env],evaluation,3);assert ev.fingerprint(env)==fingerprint
 result['metrics']=harness.metrics(result);harness.write(out/'result.json',result);print('RETRY',n,rel,result['valid'],flush=True)
