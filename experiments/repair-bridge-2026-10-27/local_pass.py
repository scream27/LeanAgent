"""Bounded deterministic post-pass on the common harness's actual observations.
No fabricated failures, no model calls, no query proof can become a submission.
"""
import json, re, sys
from pathlib import Path
from bridge import HERE, REPO, PreparedEvaluator, harness
from lean_agent.evaluator.lean import execute, render, sha256
from lean_agent.evaluator.tokens import proof_body

def explicit_suggestion(log, expected_line=None):
    if expected_line is not None:
        messages=re.split(r"(?m)(?=^.*?\.lean:\d+:\d+: (?:info|information|warning|error):)",log)
        log="\n".join(m for m in messages if (p:=re.search(r"\.lean:(\d+):\d+:",m)) and int(p[1])==expected_line)
    suggestions=re.findall(r'Try this:\s*(?:\[apply\]\s*)?([^\n]+)',log)
    if len(suggestions)!=1: return None
    s=suggestions[0].strip()
    if not s.startswith(('exact ','simp only ','simp_all only ')): return None
    if re.search(r'\b(sorry|admit)\b',s): return None
    return s

def raw_logs(result,folder):
    return '\n'.join((folder/label/r['log']).read_text() for label,row in result.get('environments',{}).items() for r in row.get('runs',[]) if (folder/label/r['log']).exists())

def proposals(body,valid):
    if not valid:
        # Preserve the existing strategy and try to close the remaining goals.
        # These are whole-body candidates, not certified local-state repairs.
        for tactic in ['assumption','rfl','exact?','simp?',
                       'simp_all [List.Subset, or_imp]',
                       "(repeat\u0027 apply List.Subset.app) <;> (try (apply List.Subset.trans; assumption)) <;> simp +contextual [List.Subset, or_imp]"]:
            yield 'append_remaining_goals',body.rstrip()+'\n  all_goals '+tactic+'\n',tactic.endswith('?'),None
    else:
        # Conservative standalone one-line sites; no AST/dependency claim here.
        sites=[(i,l) for i,l in enumerate(body.splitlines(True)) if re.fullmatch(r'\s+(?:simp(?:_all)?(?: at \w+)?|exact .+)\s*\n?',l)]
        lines=body.splitlines(True)
        for i,l in sites[:2]:
            yield 'delete_standalone_line',''.join(lines[:i]+lines[i+1:]),False,i
            if l.strip().startswith('simp'):
                changed=lines.copy();changed[i]=re.sub(r'\bsimp_all\b|\bsimp\b',lambda m:m[0]+'?',l,count=1)
                yield 'extract_simp',''.join(changed),True,i

def run(n):
    raw=REPO/'runs/repair-bridge-2026-10-27'/str(n)/'raw'
    out=raw.parent/'local'
    if (out/'summary.json').exists(): return harness.read(out/'summary.json')
    if out.exists(): raise RuntimeError('Incomplete local run; preserve logs')
    out.mkdir(parents=True)
    problem=harness.read(raw/'input/problem.json');config=harness.read(raw/'input/config.json')
    env={'id':'fixed','project':str(raw/'input/project'),'template':(raw/'input/context.lean.in').read_text(),**{k:config['lean'][k] for k in ('toolchain','command','timeout_seconds')}}
    evaluator=PreparedEvaluator()
    base_result=harness.read(raw/'baseline/result.json')
    evaluator.baseline_axioms={'fixed':set(base_result['environments']['fixed']['runs'][1]['measurement']['axioms'])}
    before=evaluator.fingerprint(env);harness.write(out/'environment.json',before)
    summary=harness.read(raw/'summary.json');baseline=summary['baseline'];best=summary['state']['best']
    observations=[];valid_pool=[];seen=set()
    for step in range(1,4):
        folder=raw/'steps'/f'{step:03}';code=(folder/'candidate.lean').read_text()
        obs=harness.read(folder/'evaluation/result.json');body=proof_body(code,problem['statement']).strip()
        for j,(op,proposed,query,line) in enumerate(proposals(body,obs['valid']),1):
            if sha256(proposed) in seen: continue
            seen.add(sha256(proposed));dest=out/f'step-{step}-attempt-{j}'
            newcode=problem['statement']+' := '+proposed
            # Query is diagnostic only, no measurement and never a pool entry.
            if query:
                dest.mkdir();source=render(env['template'],newcode,problem['name'],None)
                p=dest/'query.lean';p.write_text(source)
                invocation=execute([*env['command'],'--root='+str(dest.resolve()),str(p.resolve())],evaluator.project,env['timeout_seconds'])
                (dest/'query.log').write_text(invocation['output']);harness.write(dest/'invocation.json',invocation)
                body_start=source.index(newcode)+len(problem['statement'])+4
                query_index=proposed.rfind('all_goals') if line is None else sum(len(l) for l in proposed.splitlines(True)[:line])
                expected_line=source[:body_start+query_index].count('\n')+1
                suggestion=explicit_suggestion(invocation['output'],expected_line)
                item={'source_step':step,'operator':op,'query':True,'query_returncode':invocation['returncode'],'suggestion':suggestion,'log':str((dest/'query.log').relative_to(REPO)),'outcome':'no_supported_suggestion'}
                if suggestion:
                    lines=proposed.splitlines(True)
                    if line is None: lines[-1]='  all_goals '+suggestion+'\n'
                    else: lines[line]=re.match(r'\s*',lines[line])[0]+suggestion+'\n'
                    proposed=''.join(lines);newcode=problem['statement']+' := '+proposed
                    result=evaluator.evaluate(newcode,problem,[env],dest/'explicit',3)
                    harness.write(dest/'explicit/result.json',result)
                    item.update(outcome='valid' if result['valid'] else 'invalid',result=result)
            else:
                result=evaluator.evaluate(newcode,problem,[env],dest,3)
                harness.write(dest/'result.json',result)
                item={'source_step':step,'operator':op,'query':False,'outcome':'valid' if result['valid'] else 'invalid','result':result,'log':str(dest.relative_to(REPO))}
            if item['outcome']=='valid':
                value=harness.candidate(newcode,item['result'],baseline)
                item['metrics']=harness.metrics(item['result']);item['candidate_sha256']=value['sha256']
                (dest/'explicit-candidate.lean').write_text(newcode)
                valid_pool.append(value)
                if harness.ranking(value)<harness.ranking(best): best=value
            observations.append(item)
            (out/'progress.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2))
            print('LOCAL',n,step,j,op,item['outcome'],flush=True)
    final=evaluator.evaluate(best['code'],problem,[env],out/'final',3);harness.write(out/'final/result.json',final)
    if evaluator.fingerprint(env)!=before: raise RuntimeError('Prepared dependency closure changed')
    if not final['valid']: raise RuntimeError('Selected proof failed final validation')
    (out/'selected.lean').write_text(best['code'])
    result={'problem_id':n,'baseline':baseline,'before':summary['state']['best'],'after':best,'final':harness.metrics(final),'final_valid':True,'attempts':observations,'valid_pool':valid_pool,'api_calls':0,'official_evaluation':False,'scope':'bounded whole-body repair and standalone-line cleanup; no certified local goal snapshots'}
    harness.write(out/'summary.json',result)
    (out/'local_pass.py').write_bytes(Path(__file__).read_bytes());(out/'bridge.py').write_bytes((HERE/'bridge.py').read_bytes());harness.seal(out)
    return result
if __name__=='__main__':
 for n in map(int,sys.argv[1:] or ['1','2']):run(n)
