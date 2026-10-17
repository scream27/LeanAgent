"""Whole-file compilation in disposable copies, with separate axiom auditing."""
from pathlib import Path
import re
import shutil
import tempfile
from .common import git, read, run, save, sha, write
from .mining import mask_comments

ALLOWED_AXIOMS = {'propext', 'Classical.choice', 'Quot.sound'}
FORBIDDEN = re.compile(r'\b(sorry|sorryAx|admit|axiom|unsafe|native_decide|ofReduceBool|ofReduceNat|'
    r'import|prelude|set_option|theorem|lemma|def|opaque|abbrev|instance|namespace|section|end|'
    r'open|export|variable|variables|universe|universes|constant|constants|axioms|class|'
    r'structure|inductive|mutual|deriving|example|'
    r'elab|elab_rules|macro|macro_rules|syntax|notation|run_tac|run_elab|run_cmd|initialize|'
    r'attribute|extern|implemented_by)\b|#|```|\bIO\.')


def safety(body, name):
    try: code = mask_comments(body)
    except ValueError: return ['unclosed comment or string']
    reasons = []
    if not code.strip(): reasons.append('empty proof')
    if FORBIDDEN.search(code): reasons.append('forbidden construct or environment modification')
    short = name.rsplit('.', 1)[-1]
    if re.search(r"(?<![\w'])" + re.escape(short) + r"(?![\w'])", code):
        reasons.append('target theorem self-reference')
    return reasons


def classify(output, timed_out=False):
    if timed_out: return 'resource_exhaustion'
    rules = [('resource_exhaustion', r'heartbeats|maximum recursion|out of memory|stack overflow'),
             ('syntax_errors', r'unexpected token|unexpected end|expected token|unterminated|parser error'),
             ('unknown_identifiers', r'unknown identifier|unknown constant|unknown tactic|unknown namespace'),
             ('type_mismatches', r'type mismatch|application type mismatch|failed to synthesize'),
             ('unsolved_goals', r'unsolved goals'),
             ('tactic_failures', r'tactic.*failed|`(?:grind|simp|omega|aesop|exact|apply|rw)` failed|omega could not prove|case tag .* not found|simp made no progress|no goals to be solved')]
    for category, pattern in rules:
        if re.search(pattern, output, re.I): return category
    return 'other_errors'


def splice(source, row, body):
    a, b = row['proof_start'], row['proof_end']
    if sha(source) != row['source_sha256'] or source[a:b] != row['reference_proof']:
        raise ValueError('Source or proof span changed')
    return source[:a] + body + source[b:]


def verify(repo, row, body, folder, timeout=180):
    repo, folder = Path(repo).resolve(), Path(folder)
    if git(repo, 'rev-parse', 'HEAD').strip() != row['source_commit']:
        raise ValueError('Wrong Strata revision')
    if read(repo / 'lean-toolchain').strip() != row['lean_version']:
        raise ValueError('Wrong Lean toolchain')
    if git(repo, 'status', '--porcelain', '--untracked-files=no').strip():
        raise ValueError('Verification requires a clean pinned repository')
    source = git(repo, 'show', f"{row['source_commit']}:{row['source_file']}")
    candidate = splice(source, row, body)
    write(folder / 'source.lean', candidate)
    reasons = safety(body, row['theorem_name'])
    # The disposable environment is independent, including compiled dependencies.
    # Never hardlink mutable files back to the original checkout.
    cache = Path('.synthetic-cache').resolve()
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='verify-', dir=cache) as temporary:
        work = Path(temporary)
        for item in repo.iterdir():
            if item.name == '.git': continue
            if item.is_dir(): shutil.copytree(item, work / item.name)
            else: shutil.copy2(item, work / item.name)
        target = work / row['source_file']
        write(target, candidate)
        start_hashes = {str(p.relative_to(work)): sha(read(p)) for p in work.rglob('*.lean')}
        version = run(['lake', 'env', 'lean', '--version'], work)
        if row['lean_version'].split(':')[-1].lstrip('v') not in version['stdout']:
            raise RuntimeError('Executed Lean version does not match pin: ' + str(version))
        result = run(['lake', 'env', 'lean', row['source_file']], work, timeout)
        save(folder / 'compile.json', result)
        write(folder / 'stdout.log', result['stdout'])
        write(folder / 'stderr.log', result['stderr'])
        diagnostics = result['stdout'] + result['stderr']
        compiled = result['exit_code'] == 0 and not result['timed_out']
        # An additional audit invocation leaves the authoritative source intact.
        # Insert print immediately after target, before any namespace ends.
        audit_text = candidate[:row['proof_start'] + len(body)] + '\n#print axioms ' + row['theorem_name'] + '\n' + candidate[row['proof_start'] + len(body):]
        axioms, axiom_ok = None, None
        if compiled:
            write(target, audit_text)
            audit = run(['lake', 'env', 'lean', row['source_file']], work, timeout)
            save(folder / 'axioms.json', audit)
            axout = audit['stdout'] + audit['stderr']
            match = re.search(re.escape(row['theorem_name']) + r"' depends on axioms: \[([^\]]*)\]", axout, re.S)
            if match:
                axioms = [a.strip() for a in match[1].split(',') if a.strip()]
            elif f"'{row['theorem_name']}' does not depend on any axioms" in axout: axioms = []
            axiom_ok = audit['exit_code'] == 0 and axioms is not None and set(axioms) <= ALLOWED_AXIOMS
            if not axiom_ok: reasons.append('transitive axiom audit failed or unavailable')
            write(target, candidate)
        end_hashes = {str(p.relative_to(work)): sha(read(p)) for p in work.rglob('*.lean')}
        if end_hashes != start_hashes: reasons.append('environment source modified during compilation')
    infrastructure = result['exit_code'] is None or bool(re.search(r'object file .* does not exist|unknown module prefix|failed to load|no such file|could not resolve', diagnostics, re.I))
    answer = dict(compile_success=compiled, safety_passed=not reasons, safety_reasons=reasons,
        axioms=axioms, axiom_check=axiom_ok, safety_scope='lexical preflight plus transitive axioms when compiled',
        compiler_errors=diagnostics if not compiled else '', verification_time=result['elapsed_seconds'],
        error_category=None if compiled else classify(diagnostics, result['timed_out']),
        infrastructure_failure=infrastructure, heartbeats=None,
        heartbeat_status='not measured: instrumentation changes the original environment',
        source_sha256=sha(candidate), exit_code=result['exit_code'], verification_timed_out=result['timed_out'])
    save(folder / 'result.json', answer)
    return answer
