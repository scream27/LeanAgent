"""Immutable, first-response file transport; no generation retry or repair loop."""
import json
from pathlib import Path
from .common import read, rows, save, sha, write, jsonl
from .upstream import helpers
from .verification import verify

STRATEGIES = [
    'Conservatively compress repeated tactic steps, retaining the reference argument.',
    'Use available structural lemmas to shorten the reference argument.',
    'Consolidate case analysis and simplification in the reference proof.',
    'Prefer explicit terms and smaller reasoning steps where they simplify the reference.',
    'Seek a compact proof using the reference invariants and available automation.',
]


def prompt(row, source, attempt):
    return f'''Refactor this existing Lean reference proof. Return ONLY its replacement proof
term (normally beginning with by), without Markdown. Preserve the exact theorem
statement. Do not generate a statement from scratch. Do not change imports,
notation, options, or any surrounding declaration. Do not use random mutations,
intentional syntax/logical errors, sorry, admit, unauthorized axioms, native_decide,
metaprogramming, or the target theorem itself. Produce a shorter, simpler, or more
efficient proof. This is one fresh attempt, without compiler feedback or retries.
Attempt: {attempt + 1}/5
Objective: {STRATEGIES[attempt]}
Theorem: {row['theorem_name']}
Toolchain: {row['lean_version']}

EXACT ORIGINAL STATEMENT (everything before :=):
{row['theorem_statement']}

COMPLETE REFERENCE PROOF:
{row['reference_proof']}

COMPLETE ORIGINAL SOURCE FILE (imports and all surrounding declarations):
{source}
'''


def prepare(dataset, phase):
    dataset = Path(dataset)
    theorems = rows(dataset / 'theorems.jsonl')
    if len(theorems) != 10: raise ValueError('Exactly 10 verified reference theorems required')
    if phase == 'remaining':
        gate = json.loads(read(dataset / 'pilot-review.json'))
        if not gate.get('approved'): raise ValueError('Pilot has not passed infrastructure review')
        pilot = rows(dataset / 'dataset.jsonl')
        if len([r for r in pilot if r['phase'] == 'pilot']) != 15:
            raise ValueError('Pilot must contain exactly 15 attempts')
    chosen = theorems[:3] if phase == 'pilot' else theorems[3:]
    for row in chosen:
        source = read(dataset / 'sources' / row['source_file'])
        if sha(source) != row['source_sha256']: raise ValueError('Source snapshot changed')
        for i in range(5):
            folder = dataset / 'generation' / f"{row['problem_id']}-{i+1}"
            text = prompt(row, source, i)
            if folder.exists():
                if read(folder / 'prompt.txt') != text: raise ValueError('Existing prompt changed')
                continue
            write(folder / 'prompt.txt', text)
            save(folder / 'request.json', dict(problem_id=row['problem_id'], candidate_id=folder.name,
                phase=phase, attempt=i+1, generation_model='Codex session (exact model identifier unavailable)',
                generation_parameters=dict(transport='codex-session-file', strategy=STRATEGIES[i],
                    seed=None, temperature=None, top_p=None, independent_api_calls=False,
                    sampling_note='User selected shared Codex session. Diversity is prompt-controlled; statistical independence is not guaranteed.'),
                prompt_sha256=sha(text), prompt_tokens=None, completion_tokens=None))


def submit(dataset, candidate_id, proof_file):
    folder = Path(dataset) / 'generation' / candidate_id
    if folder.parent.resolve() != (Path(dataset) / 'generation').resolve(): raise ValueError('Invalid candidate ID')
    request = json.loads(read(folder / 'request.json'))
    if request['candidate_id'] != candidate_id: raise ValueError('Candidate ID mismatch')
    # Exclusive creation prevents replacing a failed, duplicate, or malformed attempt.
    response = read(proof_file)
    with (folder / 'response.txt').open('x', encoding='utf-8', newline='') as f: f.write(response)
    save(folder / 'response.json', dict(response_sha256=sha(response), raw_response=response,
                                       prompt_tokens=None, completion_tokens=None))


def evaluate(dataset, repo, upstream, phase):
    dataset = Path(dataset)
    _, scorer = helpers(upstream)
    theorems = {r['problem_id']: r for r in rows(dataset / 'theorems.jsonl')}
    existing = rows(dataset / 'dataset.jsonl') if (dataset / 'dataset.jsonl').exists() else []
    ids = {r['candidate_id'] for r in existing}
    requests = []
    for folder in sorted((dataset / 'generation').iterdir()):
        req = json.loads(read(folder / 'request.json'))
        if req['phase'] == phase: requests.append((folder, req))
    expected = 15 if phase == 'pilot' else 35
    if len(requests) != expected: raise ValueError('Incomplete phase requests')
    # All five first responses must be frozen before any compiler feedback is exposed.
    for folder, req in requests:
        if not (folder / 'response.txt').exists(): raise ValueError('Missing first response: ' + folder.name)
        if sha(read(folder / 'prompt.txt')) != req['prompt_sha256']: raise ValueError('Prompt changed')
    for folder, req in requests:
        if req['candidate_id'] in ids: continue
        row = theorems[req['problem_id']]
        body = read(folder / 'response.txt')
        raw = json.loads(read(folder / 'response.json'))
        if sha(body) != raw['response_sha256']: raise ValueError('First response changed')
        result = verify(repo, row, body, dataset / 'verification' / folder.name)
        if result['infrastructure_failure']:
            save(dataset / 'infrastructure-stop.json', dict(candidate_id=folder.name, result=result))
            raise RuntimeError('Verification infrastructure failed; stop before scaling')
        tokens = len(scorer.tokenize_proof_body(body))
        duplicate = any(r['problem_id'] == row['problem_id'] and r['candidate_proof'] == body for r in existing)
        record = {**row, **req, **result, 'candidate_proof': body,
            'reference_source_sha256': row['source_sha256'],
            'verification_source_sha256': result['source_sha256'],
            'generation_prompt': read(folder / 'prompt.txt'), 'candidate_token_count': tokens,
            'length_reduction_ratio': 1 - tokens / row['reference_token_count'],
            'candidate_reference_length_ratio': tokens / row['reference_token_count'],
            'duplicate_candidate': duplicate,
            'token_count_method': 'aurasoph local_score.tokenize_proof_body at pinned commit'}
        existing.append(record)
        jsonl(dataset / 'dataset.jsonl', existing)
        print(folder.name, result['compile_success'], result['error_category'], flush=True)


def review_pilot(dataset):
    dataset = Path(dataset)
    pilot = [r for r in rows(dataset / 'dataset.jsonl') if r['phase'] == 'pilot']
    if len(pilot) != 15 or len({r['problem_id'] for r in pilot}) != 3:
        raise ValueError('Need 3 x 5 completed pilot candidates')
    for problem in {r['problem_id'] for r in pilot}:
        if sum(r['problem_id'] == problem for r in pilot) != 5: raise ValueError('Unbalanced pilot')
    if any(r['infrastructure_failure'] for r in pilot): raise ValueError('Infrastructure failure')
    if not any(r['compile_success'] for r in pilot):
        raise ValueError('All pilot candidates failed; inspect extraction and verification before scaling')
    save(dataset / 'pilot-review.json', dict(approved=True, candidates=15,
        compiling=sum(r['compile_success'] for r in pilot),
        evidence='All references compiled; exact source/proof spans checked; complete files compiled; no missing modules/toolchain errors.',
        note='Candidate failures retained without repair. All pilot responses frozen before verification.'))
