"""Audit the stored artifacts without rerunning or repairing any proof."""
import json
from collections import Counter
from pathlib import Path
from .common import read, rows, sha, save, jsonl
from .verification import splice, classify, safety
from .upstream import helpers


def reclassify(dataset):
    """Derived categories may evolve; raw compiler evidence is immutable."""
    dataset = Path(dataset)
    data = rows(dataset/'dataset.jsonl')
    refs = {r['problem_id']: r for r in rows(dataset/'theorems.jsonl')}
    changes = []
    for row in data:
        compile_log = json.loads(read(dataset/'verification'/row['candidate_id']/'compile.json'))
        category = None if row['compile_success'] else classify(row['compiler_errors'], compile_log['timed_out'])
        if category != row['error_category']:
            changes.append(dict(candidate_id=row['candidate_id'], old=row['error_category'], new=category))
            row['error_category'] = category
        row['verification_timed_out'] = compile_log['timed_out']
        row['reference_source_sha256'] = refs[row['problem_id']]['source_sha256']
        row['verification_source_sha256'] = sha(read(dataset/'verification'/row['candidate_id']/'source.lean'))
    if changes:
        path = dataset/'error-reclassification.json'
        prior = json.loads(read(path))['changes'] if path.exists() else []
        save(path, dict(reason='Expand classification from observed compiler diagnostics; raw logs unchanged', changes=prior+changes))
    jsonl(dataset/'dataset.jsonl', data)


def validate(dataset, upstream, expected=50):
    dataset = Path(dataset)
    data, refs = rows(dataset/'dataset.jsonl'), rows(dataset/'theorems.jsonl')
    _, score = helpers(upstream)
    if len(data) != expected: raise ValueError(f'Expected {expected} candidates, got {len(data)}')
    if len(refs) != 10: raise ValueError('Expected ten references')
    if len({r['candidate_id'] for r in data}) != len(data): raise ValueError('Duplicate candidate IDs')
    if expected == 50 and set(Counter(r['problem_id'] for r in data).values()) != {5}:
        raise ValueError('Each theorem must have exactly five attempts')
    excluded = json.loads(read(dataset/'exclusions.json'))['files']
    references = {r['problem_id']: r for r in refs}
    for ref in refs:
        if ref['source_file'] in excluded: raise ValueError('Warm-up source leakage')
        if ref['proof_lines'] <= 30: raise ValueError('Short reference')
        if not ref['reference_verification']['compile_success']: raise ValueError('Unverified reference')
        source = read(dataset/'sources'/ref['source_file'])
        if splice(source, ref, ref['reference_proof']) != source: raise ValueError('Reference splice mismatch')
    seen = set()
    for row in data:
        ref = references[row['problem_id']]
        folder = dataset/'generation'/row['candidate_id']
        if row['candidate_proof'] != read(folder/'response.txt'): raise ValueError('Candidate was edited')
        if row['generation_prompt'] != read(folder/'prompt.txt'): raise ValueError('Prompt mismatch')
        for key in ('theorem_statement', 'reference_proof', 'source_commit', 'source_file', 'lean_version'):
            if row[key] != ref[key]: raise ValueError(f'Reference metadata changed: {key}')
        response = json.loads(read(folder/'response.json'))
        if response['response_sha256'] != sha(row['candidate_proof']): raise ValueError('Response hash mismatch')
        source = read(dataset/'sources'/ref['source_file'])
        expected_source = splice(source, ref, row['candidate_proof'])
        verification = dataset/'verification'/row['candidate_id']
        if expected_source != read(verification/'source.lean'): raise ValueError('Outside-proof modification')
        log = json.loads(read(verification/'compile.json'))
        if row['compile_success'] != (log['exit_code'] == 0 and not log['timed_out']):
            raise ValueError('Compile label does not match Lean exit status')
        if row['verification_time'] != log['elapsed_seconds']: raise ValueError('Elapsed time mismatch')
        category = None if row['compile_success'] else classify(row['compiler_errors'], log['timed_out'])
        if row['error_category'] != category: raise ValueError('Stale error classification; run reclassify')
        if row['compile_success'] and row['safety_passed'] and not row['axiom_check']:
            raise ValueError('Missing axiom audit')
        if row['safety_passed'] and safety(row['candidate_proof'], row['theorem_name']):
            raise ValueError('Safety label disagrees with preflight')
        for field, body in [('reference_token_count', ref['reference_proof']), ('candidate_token_count', row['candidate_proof'])]:
            if row[field] != len(score.tokenize_proof_body(body)): raise ValueError('Token count mismatch')
        ratio = 1-row['candidate_token_count']/row['reference_token_count']
        if row['length_reduction_ratio'] != ratio: raise ValueError('Ratio mismatch')
        key = (row['problem_id'], row['candidate_proof'])
        if row['duplicate_candidate'] != (key in seen): raise ValueError('Duplicate label mismatch')
        seen.add(key)
    result = dict(passed=True, references=len(refs), candidates=len(data),
                  checks='counts, exclusions, reference verification, source spans, immutable responses, prompts, compiler exits, axiom audits, tokens, ratios, duplicates')
    save(dataset/'integrity.json', result)
    return result
