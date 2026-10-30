"""Audit actual artifacts, invariant context, selection, axioms and response format."""
import json
from bridge import HERE,REPO,harness
from lean_agent.evaluator.lean import render,sha256
from lean_agent.evaluator.tokens import validate_declaration,proof_body

def audit():
    checks=[]
    def check(label,value):
        checks.append({'check':label,'passed':bool(value)})
    report=harness.read(HERE/'refactoring_results.json')
    for p in report['problems']:
        n=p['id'];root=REPO/'runs/repair-bridge-2026-10-27'/str(n);raw=root/'raw';local=root/'local'
        check(f'{n}: raw replay',harness.replay(raw)['record_replay_passed'])
        inventory=harness.read(local/'artifacts.json')
        actual={str(p.relative_to(local)):sha256(p.read_bytes()) for p in local.rglob('*') if p.is_file() and p.name!='artifacts.json' and '__pycache__' not in p.parts}
        check(f'{n}: local artifact hashes',inventory==actual)
        problem=harness.read(raw/'input/problem.json');template=(raw/'input/context.lean.in').read_text()
        original=render(template,problem['reference'],problem['name'],None)
        a=original.index(problem['reference'])+len(problem['statement'])
        end=original.index(problem['reference'])+len(problem['reference'])
        base=harness.read(raw/'baseline/result.json');allowed=set(base['environments']['fixed']['runs'][1]['measurement']['axioms'])
        for stage in ['raw','local']:
            d=root/stage
            code=(d/'selected.lean').read_text();validate_declaration(code,problem['statement'])
            check(f'{n}: {stage} fixed statement',code.startswith(problem['statement']+' :='))
            target=render(template,code,problem['name'],None)
            check(f'{n}: {stage} fixed surrounding source',target==original[:a]+code[len(problem['statement']):]+original[end:])
            result=harness.read(d/'final/result.json');check(f'{n}: {stage} final valid',result['valid'])
            check(f'{n}: {stage} three samples',len([r for r in result['environments']['fixed']['runs'] if 'measurement'in r])==3)
            for r in result['environments']['fixed']['runs']:
                if 'measurement' in r:check(f'{n}: {stage} axiom allowance',set(r['measurement']['axioms'])<=allowed)
        result=harness.read(local/'summary.json')
        check(f'{n}: retained best by common ranking',harness.ranking(result['after'])<=harness.ranking(result['before']))
        response=harness.read(HERE/f'p{n}.response.json')
        check(f'{n}: response schema',set(response)=={'proof'})
        check(f'{n}: exported proof matches selection',response['proof']==proof_body(result['after']['code'],problem['statement']).strip())
        check(f'{n}: measured candidates contain no query tactic',not any(t in response['proof'] for t in ('simp?','exact?','aesop?')))
        check(f'{n}: adapter was archived',sha256((root/'bridge.py').read_bytes())==harness.read(raw/'manifest.json')['environment']['adapter_sha256'])
    followup=REPO/'runs/repair-bridge-2026-10-27/1/json-query-followup'
    if (followup/'summary.json').exists():
        data=harness.read(followup/'summary.json');check('JSON followup environment stable',data['environment_unchanged'])
        inventory=harness.read(followup/'artifacts.json')
        actual={str(p.relative_to(followup)):sha256(p.read_bytes()) for p in followup.rglob('*') if p.is_file() and p.name!='artifacts.json'}
        check('JSON followup artifact hashes',inventory==actual)
        for i,item in enumerate(data['results']):
            check(f'JSON {i}: matched source location',len(item['matched_messages'])==1 and item['matched_messages'][0]['pos']['line']==item['expected_line'])
            check(f'JSON {i}: explicit replay valid',item['result']['valid'])
            check(f'JSON {i}: no missed better candidate',item['beats_selected'] is False)
    outcome={'checks':len(checks),'passed':all(c['passed'] for c in checks),'issues':[c for c in checks if not c['passed']],'records':checks}
    (HERE/'audit.json').write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in outcome.items() if k!='records'}));assert outcome['passed']
if __name__=='__main__':audit()
