"""Pinned-context Lean verification and local measurements; never calls an LLM.

Run one environment at a time: python run_sweep.py SOURCE VERSION PROJECT_DIR [ID ...]
Results remain append-only per candidate/version. Artifact files are not submissions.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ['TIKTOKEN_CACHE_DIR'] = str(HERE / 'tokenizer_cache')
import tiktoken
ENC = tiktoken.get_encoding('o200k_base')
ROWS = [json.loads(l) for l in (HERE / 'reference' / 'benchmark_data_warmup.jsonl').read_text().splitlines()]
CANDIDATES = [json.loads(l) for l in (HERE / 'candidates.jsonl').read_text().splitlines()]
MEASURE = '''
elab "#arena_count " cmd:command : command => do
  let start ← IO.getNumHeartbeats
  Lean.Elab.Command.elabCommand (← `(command| set_option Elab.async false in $cmd))
  let finish ← IO.getNumHeartbeats
  Lean.logInfo m!"ARENA_HEARTBEATS_RAW={finish - start}"

'''


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def invoke(project, text, dest, output_olean=False, search_dir=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    path = dest.with_suffix('.lean')
    path.write_text(text)
    env = dict(os.environ)
    # Reuse the user's existing 4.26 installation; other toolchains are isolated.
    if 'v4.26.0' not in (project / 'lean-toolchain').read_text():
        env['ELAN_HOME'] = str(HERE / 'environments/elan')
    if search_dir:
        env['LEAN_PATH']=str(search_dir)+os.pathsep+env.get('LEAN_PATH','')
    cmd = [str(Path.home()/'.elan/bin/lake'), 'env', 'lean']
    if output_olean:
        cmd += ['-R',str(dest.parent),'-o',str(dest.with_suffix('.olean'))]
    cmd += [str(path)]
    t = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=project, env=env, capture_output=True, text=True, timeout=180)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc = None
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout or ''
        err = 'TIMEOUT: 180s operational limit (not an Arena limit)'
    dest.with_suffix('.stdout.txt').write_text(out)
    dest.with_suffix('.stderr.txt').write_text(err)
    obs = {'command': cmd, 'cwd': str(project), 'returncode': rc,
           'wall_seconds': time.monotonic()-t, 'stdout_path': str(dest.with_suffix('.stdout.txt')),
           'stderr_path': str(dest.with_suffix('.stderr.txt'))}
    save(dest.with_suffix('.run.json'), obs)
    return rc, out, err


def inspect_output(rc, out, err, name):
    pattern = re.escape(name) + r"'? depends on axioms: \[([^\]]*)\]"
    matches = re.findall(pattern, out, re.S)
    axioms = [a.strip() for a in matches[-1].replace('\n', '').split(',') if a.strip()] if matches else None
    if f"'{name}' does not depend on any axioms" in out:
        axioms = []
    if rc is None:
        kind = 'timeout'
    elif rc != 0:
        kind = 'environment_error' if any(s in out+err for s in ['object file', 'unknown module prefix', 'failed to download', 'no such file']) else 'invalid'
    elif axioms is None:
        kind = 'axiom_check_missing'
    elif set(axioms) - {'propext', 'Quot.sound', 'Classical.choice'}:
        kind = 'invalid_axioms'
    else:
        kind = 'valid'
    return {'kind': kind, 'axioms': axioms}


def context(row, project, version):
    if row['source'] == 'putnambench':
        source = row['header'] + '\n' + row['src'] + '\n'
    else:
        commit = next(pair[version] for pair in row['version_info'] if version in pair)
        source = subprocess.check_output(['git', 'show', commit+':'+row['file_path']], cwd=project, text=True)
    if source.count(row['src']) != 1 and row['name'].endswith('fiberwise_dist_lt_imp_dist_lt_unique_decoding_radius'):
        # Inspected old commits differ by exactly this extra body-space. No
        # whitespace fuzzing of statements, strings, comments or arbitrary proofs.
        old=row['src'].replace('have h_elemenet_Y_bad : y_of_x', 'have h_elemenet_Y_bad :  y_of_x')
        if source.count(old)==1:
            source=source.replace(old,row['src'],1)
    if source.count(row['src']) != 1:
        # No fuzzy theorem matching or guessing body ranges across revisions.
        raise ValueError('Exact benchmark declaration not uniquely present in pinned source')
    decl_start = source.index(row['src'])
    tail = row['src'][len(row['statement']):]
    assert tail.lstrip().startswith(':=')
    body = tail.lstrip()[2:].lstrip()
    body_start = decl_start + len(row['src']) - len(body)
    body_end = decl_start + len(row['src'])
    assert source[body_start:body_end] == body
    return source, body_start, body_end, decl_start, body


def check(row, project, version, body, dest, ctx, measure=True):
    source, a, b, ds, original = ctx
    file = source[:a] + body + source[b:]
    # These authored candidates contain no commands in their bodies. Reject obvious
    # command injection; this is not a replacement for a general Lean AST firewall.
    forbidden = re.search(r'\b(sorry|admit|sorryAx|native_decide|unsafe|axiom)\b|^\s*(?:import|theorem|lemma|def|elab|macro|initialize|set_option)\b', body, re.M)
    if forbidden:
        return {'kind': 'contract_reject', 'reason': forbidden.group()}
    is_module=bool(re.search(r'^module\s*$',file,re.M))
    if is_module:
        rc,out,err=invoke(project,file,dest,output_olean=True)
        if rc==0:
            probe=f'import {dest.name}\n#print axioms {row["name"]}\n'
            prc,pout,perr=invoke(project,probe,Path(str(dest)+'_axioms'),search_dir=dest.parent)
            out+='\n'+pout;err+='\n'+perr
            if prc: rc=prc
        combined=dest.with_suffix('.combined.txt');combined.write_text(out)
    else:
        rc, out, err = invoke(project, file + '\n#print axioms ' + row['name']+'\n', dest)
    res = inspect_output(rc, out, err, row['name'])
    res.update(body_hash=sha(body), tokens=len(ENC.encode(body)), output_path=str(dest.with_suffix('.combined.txt' if is_module else '.stdout.txt')))
    if res['kind'] == 'valid' and measure:
        # Add instrumentation only to a separate copy. Measure the declaration,
        # synchronously, with the original resource options retained.
        # The whole uninstrumented file was already verified above. Stop this
        # separate measurement copy immediately after the target declaration:
        # the custom command can affect section-variable tracking for later
        # `omit ... in` commands, which are outside the measured declaration.
        measured = source[:ds] + MEASURE + '#arena_count\n' + file[ds:a+len(body)] + '\n#exit\n'
        lines = measured.splitlines(True)
        module_lines=[i for i,l in enumerate(lines) if l.strip()=='module']
        k = module_lines[0]+1 if module_lines else 0
        lines.insert(k, 'import Lean\n')
        mrc, mout, merr = invoke(project, ''.join(lines), Path(str(dest)+'_measure'))
        counts = re.findall(r'ARENA_HEARTBEATS_RAW=(\d+)', mout)
        res['heartbeats_raw'] = int(counts[-1]) if mrc == 0 and counts else None
        res['heartbeats'] = res['heartbeats_raw']/1000 if res['heartbeats_raw'] is not None else None
        res['measurement_kind'] = 'local_o200k_base_and_synchronous_declaration_heartbeats'
    return res


def local_pass(row, project, version, candidate, obs, d, ctx):
    """Finite operators fixed across problems; proposals always require full replay.

    No tactic-state certificate is fabricated. This runner only certifies whole
    candidate outcomes. At most two bare automation sites are queried per body.
    """
    body = candidate['proof_body']
    attempts, derived = [], []
    if candidate.get('user_excluded') or body == ctx[-1]:
        return {'state': 'not_applicable', 'attempts': [], 'derived': [],
                'reason': 'Original body retained; no modification requested for this candidate'}
    if obs['kind'] == 'valid':
        sites = [(i,l) for i,l in enumerate(body.splitlines())
                 if re.fullmatch(r'\s*(simp|simp_all|aesop)\s*',l)][:2]
        for k,(i,line) in enumerate(sites):
            query_lines=body.splitlines()
            query_lines[i]=line.rstrip()+'?'
            queried='\n'.join(query_lines)+'\n'
            dest=d/f'extract{k}_query'
            q=check(row,project,version,queried,dest,ctx,measure=False)
            entry={'operator':'extract_automation','body_line':i,'query':query_lines[i], 'observation':q}
            out=dest.with_suffix('.stdout.txt').read_text() if dest.with_suffix('.stdout.txt').exists() else ''
            # Only a one-line suggestion is accepted by v1. Multiline scripts are
            # left for an AST-aware extractor; never truncate and assume success.
            match=re.search(r'Try this:\s*(?:\[apply\]\s*)?([^\n]+)',out)
            if match:
                suggestion=match.group(1).strip()
                if suggestion.startswith(('simp only','simp_all only','exact ','aesop ')):
                    patched=body.splitlines()
                    patched[i]=line[:len(line)-len(line.lstrip())]+suggestion
                    newbody='\n'.join(patched)+'\n'
                    checked=check(row,project,version,newbody,d/f'extract{k}_replay',ctx)
                    entry.update(suggestion=suggestion,replay=checked)
                    if checked['kind']=='valid':
                        derived.append({'proof_body':newbody,'observation':checked,'origin':'extraction'})
            attempts.append(entry)
    elif obs['kind'] in {'invalid','invalid_axioms'}:
        # One-line replacement only when the diagnostic points inside the body
        # and the line has no indented continuation. Otherwise try whole-body solvers.
        text=Path(obs['output_path']).read_text()
        errors=re.findall(r':(\d+):\d+: error[^:]*:',text)
        bodyline=ctx[0][:ctx[1]].count('\n')+1
        index=int(errors[0])-bodyline if errors else -1
        lines=body.splitlines()
        site_ok=(0 < index < len(lines) and not lines[index].lstrip().startswith(('case ','|','next '))
                 and (index+1==len(lines) or len(lines[index+1])-len(lines[index+1].lstrip()) <= len(lines[index])-len(lines[index].lstrip())))
        for k,tactic in enumerate(['assumption','rfl','omega','simp?','exact?','aesop?']):
            if site_ok:
                patched=list(lines)
                prefix=re.match(r'\s*(?:[·.]\s+)?',lines[index]).group()
                patched[index]=prefix+tactic
                proposal='\n'.join(patched)+'\n'
            else:
                proposal='by\n  '+tactic+'\n'
            checked=check(row,project,version,proposal,d/f'repair{k}',ctx,measure=False)
            entry={'operator':'single_line_solver' if site_ok else 'whole_body_solver',
                   'tactic':tactic,'observation':checked}
            attempts.append(entry)
            if checked['kind']=='valid':
                checked=check(row,project,version,proposal,d/f'repair{k}_measure_replay',ctx)
                derived.append({'proof_body':proposal,'observation':checked,'origin':'local_repair',
                                'search_query_only':tactic.endswith('?')})
                # Successful ? proposals need extraction; keep the raw valid body
                # as well, and never treat a partial suggestion as a closed proof.
                if tactic.endswith('?'):
                    output=(d/f'repair{k}.stdout.txt').read_text()
                    match=re.search(r'Try this:\s*(?:\[apply\]\s*)?([^\n]+)',output)
                    if match and match.group(1).strip().startswith(('simp only','exact ','simp_all only')):
                        explicit=proposal.replace(tactic,match.group(1).strip(),1)
                        expobs=check(row,project,version,explicit,d/f'repair{k}_explicit',ctx)
                        if expobs['kind']=='valid':
                            derived.append({'proof_body':explicit,'observation':expobs,'origin':'repair_extraction'})
                break
    return {'state':'exhausted' if attempts else 'not_applicable', 'attempts':attempts,
            'derived':derived,'reason':'Fixed v1 operators; no model repair calls'}


def run(source_name, version, project, ids):
    project = Path(project).resolve()
    for n, row in enumerate(ROWS, 1):
        if row['source'] != source_name or (ids and n not in ids) or not any(version in p for p in row['version_info']):
            continue
        d = HERE/'runs'/f'{n:02d}'/version
        if (d/'results.json').exists():
            old=json.loads((d/'results.json').read_text())
            if old.get('status')=='observed' and old.get('baseline',{}).get('heartbeats') is not None:
                # A primary environment may be repaired after older versions were
                # already checked. Backfill only missing identical derived bodies.
                if version != next(iter(row['version_info'][0])):
                    ctx=context(row,project,version)
                    for entry in old['candidates']:
                        catalog=HERE/'derived_candidates'/f'{n:02d}'/(entry['prompt_id']+'.json')
                        local=entry.setdefault('local',{'state':'not_applicable','attempts':[], 'derived':[]})
                        known={z['proof_body'] for z in local.get('derived',[])}
                        if catalog.exists():
                            for k,derived in enumerate(json.loads(catalog.read_text())):
                                if derived['proof_body'] in known: continue
                                checked=check(row,project,version,derived['proof_body'],d/(entry['prompt_id']+f'_backfill{k}'),ctx)
                                local.setdefault('derived',[]).append(dict(derived,observation=checked))
                    save(d/'results.json',old)
                print(n, version, 'already recorded', flush=True)
                continue
            # Preserve the initial instrument/mapping failure as evidence.
            save(d/'results.before_runner_fix.json',old)
        try:
            ctx = context(row, project, version)
        except (ValueError, subprocess.CalledProcessError) as e:
            save(d/'results.json', {'problem_id': n, 'version': version, 'status': 'context_mapping_blocked', 'reason': str(e)})
            print(n, version, 'context mapping blocked', flush=True)
            continue
        print(n, version, 'baseline', flush=True)
        baseline = check(row, project, version, ctx[-1], d/'baseline', ctx)
        result = {'problem_id': n, 'name': row['name'], 'version': version,
                  'source_hash': sha(ctx[0]), 'project': str(project), 'baseline': baseline, 'candidates': []}
        result['environment_record']={
            'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=project,text=True).strip(),
            'lean_toolchain':(project/'lean-toolchain').read_text().strip(),
            'lake_manifest_sha256':sha((project/'lake-manifest.json').read_text()) if (project/'lake-manifest.json').exists() else None,
            'git_status':subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=project,text=True).strip()}
        if baseline['kind'] != 'valid':
            result['status'] = 'baseline_blocked'
        else:
            result['status'] = 'observed'
            for c in [c for c in CANDIDATES if c['problem_id'] == n]:
                print(n, version, c['prompt_id'], flush=True)
                if c['proof_body'] == ctx[-1]:
                    obs = dict(baseline, reused_identical_baseline=True)
                else:
                    obs = check(row, project, version, c['proof_body'], d/c['prompt_id'], ctx)
                print(n, version, c['prompt_id'], 'local pass', flush=True)
                catalog=HERE/'derived_candidates'/f'{n:02d}'/(c['prompt_id']+'.json')
                primary=next(iter(row['version_info'][0]))
                if version == primary:
                    local=local_pass(row,project,version,c,obs,d/(c['prompt_id']+'_local'),ctx)
                    save(catalog,local['derived'])
                else:
                    local={'state':'not_applicable','attempts':[], 'derived':[],
                           'reason':'Replay the identical primary-version derived bodies; no per-version repairs'}
                    if catalog.exists():
                        for k,derived in enumerate(json.loads(catalog.read_text())):
                            checked=check(row,project,version,derived['proof_body'],d/(c['prompt_id']+f'_derived{k}'),ctx)
                            local['derived'].append(dict(derived,observation=checked))
                result['candidates'].append(dict(prompt_id=c['prompt_id'], observation=obs, local=local))
        save(d/'results.json', result)
        print(n, version, result['status'], flush=True)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], sys.argv[3], set(map(int, sys.argv[4:])))
