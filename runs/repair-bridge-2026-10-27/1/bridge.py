"""Explicit prepared-environment adapter through the public evaluator hook.
Core harness code, selection, API messages and replay remain unchanged.
"""
import hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'src'))
from lean_agent import harness
from lean_agent.evaluator.lean import LeanEvaluator, sha256
PROJECT=REPO/'artifacts/repair-bridge/strata'

def closure_fingerprint(project):
    paths=[p for p in project.rglob('*') if p.is_file() and '.git' not in p.parts
           and (p.suffix in {'.lean','.olean','.ilean','.so','.dylib','.a'} or p.name in {'lean-toolchain','lake-manifest.json','lakefile.toml'})]
    files={str(p.relative_to(project)):sha256(p.read_bytes()) for p in sorted(paths)}
    return {'files':files,'sha256':sha256(harness.canonical(files))}

class PreparedEvaluator(LeanEvaluator):
    def __init__(self,project=PROJECT):
        self.project=project.resolve()
        self.baseline_axioms=None
    def mapped(self,env):
        return {**env,'project':str(self.project)}
    def fingerprint(self,env):
        value=super().fingerprint(self.mapped(env))
        value['prepared_closure']=closure_fingerprint(self.project)
        value['adapter_sha256']=sha256(Path(__file__).read_bytes())
        value['scope']='Prepared project is external to the core input snapshot; dependency/source hashes are recorded, rebuilding is required on other hosts.'
        return value
    def evaluate(self,code,config,environments,output,runs):
        result=super().evaluate(code,config,[self.mapped(e) for e in environments],output,runs)
        axes={label:set().union(*(set(r['measurement']['axioms']) for r in row['runs'] if 'measurement' in r))
              for label,row in result['environments'].items()}
        if output.name=='baseline' and result['valid']:
            self.baseline_axioms=axes
        if result['valid'] and self.baseline_axioms is not None:
            for label,axioms in axes.items():
                if not axioms<=self.baseline_axioms[label]:
                    result['valid']=False
                    result['environments'][label].update(valid=False,error={'kind':'axiom_regression','message':'New axioms relative to baseline'})
                    result['error']={'kind':'axiom_regression','message':'New axioms relative to baseline'}
        return result

def run_raw(n):
    output=REPO/'runs/repair-bridge-2026-10-27'/str(n)/'raw'
    if output.exists():
        if not (output/'summary.json').exists(): raise RuntimeError('Incomplete run; preserve and use a new directory')
        return harness.read(output/'summary.json')
    result=harness.run(HERE/'inputs'/str(n)/'config.json',output,evaluator=PreparedEvaluator())
    harness.write(output/'record-replay.json',harness.replay(output))
    # Snapshot the adapter as well as the untouched common harness.
    (output/'code/bridge.py').write_bytes(Path(__file__).read_bytes())
    harness.seal(output)
    print('RAW DONE',n,result['final_valid'],flush=True)
    return result
if __name__=='__main__':
    for n in map(int,sys.argv[1:] or ['1','2']): run_raw(n)
