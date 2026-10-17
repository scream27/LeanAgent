"""Conservative line-span mining using the audited upstream scanner."""
import re
from pathlib import Path
from .common import git, read, rows, sha, jsonl, save, write
from .upstream import helpers


def mask_comments(text):
    # Preserve positions, handle nested block comments and quoted strings.
    out = list(text)
    i, depth, string = 0, 0, False
    while i < len(text):
        if depth:
            if text.startswith('/-', i):
                out[i:i+2] = '  '; depth += 1; i += 2
            elif text.startswith('-/', i):
                out[i:i+2] = '  '; depth -= 1; i += 2
            else:
                if text[i] not in '\r\n': out[i] = ' '
                i += 1
        elif string:
            if text[i] == '\\': i += 2
            else:
                if text[i] == '"': string = False
                i += 1
        elif text[i] == "'" and i + 2 < len(text) and text[i+2] == "'": i += 3
        elif text[i] == '"': string = True; i += 1
        elif text.startswith('/-', i):
            out[i:i+2] = '  '; depth = 1; i += 2
        elif text.startswith('--', i):
            end = text.find('\n', i)
            if end < 0: end = len(text)
            out[i:end] = ' ' * (end-i); i = end
        else: i += 1
    if depth or string: raise ValueError('Unclosed source comment/string')
    return ''.join(out)


def inventory(repo, upstream, warmups, min_lines=31):
    miner, score = helpers(upstream)
    excluded_names, excluded_files = set(), set()
    for warmup in warmups:
        for row in rows(warmup):
            excluded_names.update([row['name'], row['name'].rsplit('.', 1)[-1]])
            if row.get('source') == 'strata' or 'strata' in row.get('url', '').lower():
                excluded_files.add(row['file_path'].replace('\\', '/'))
    commit = git(repo, 'rev-parse', 'HEAD').strip()
    toolchain = git(repo, 'show', f'{commit}:lean-toolchain').strip()
    candidates = []
    for file in git(repo, 'ls-tree', '-r', '--name-only', commit).splitlines():
        if not file.endswith('.lean') or file in excluded_files: continue
        text = git(repo, 'show', f'{commit}:{file}')
        if not re.search(r'(?m)^(theorem|lemma)\s', text): continue
        try:
            masked = mask_comments(text)
        except ValueError:
            print('Skipped unsupported lexical syntax:', file, flush=True)
            continue
        lines = text.splitlines(keepends=True)
        for decl in miner.find_declarations(masked):
            start = sum(map(len, lines[:decl['start_line']-1]))
            end = sum(map(len, lines[:decl['end_line']]))
            chunk = masked[start:end].rstrip()
            match = score.DECL_RE.search(chunk)
            if not match or match.group(1) not in ('theorem', 'lemma'): continue
            short = match.group(2)
            # Upstream's stack does not track mutual/end; derive names from a
            # corrected scope stack while retaining its declaration spans.
            scopes = []
            for line in masked[:start].splitlines():
                scope = re.match(r'^(namespace|section|mutual|end)\b(?:\s+(\S+))?', line)
                if not scope: continue
                kind, value = scope.groups()
                if kind == 'end':
                    if scopes: scopes.pop()
                else: scopes.append((kind, value))
            prefix = '.'.join(v for k, v in scopes if k == 'namespace' and v)
            name = '.'.join(filter(None, [prefix, short]))
            if name in excluded_names or short in excluded_names: continue
            body = score._body_after_defining_assign(chunk, match.start())
            if body is None: continue
            proof_start = start + len(chunk) - len(body)
            while text[proof_start].isspace(): proof_start += 1
            proof_end = start + len(chunk)
            proof = text[proof_start:proof_end]
            nonempty = sum(bool(line.strip()) for line in mask_comments(proof).splitlines())
            if nonempty < min_lines or score.forbidden_hit(proof): continue
            # Unsupported command-like tails are rejected, never guessed away.
            if re.search(r'(?m)^(#|set_option|export|initialize|mutual|termination_by)', mask_comments(proof)): continue
            statement_end = start + len(chunk) - len(body) - 2
            candidates.append(dict(problem_id='strata-' + sha(commit + file + name)[:12],
                source_repository='https://github.com/strata-org/Strata', source_commit=commit,
                source_file=file, theorem_name=name, lean_version=toolchain,
                theorem_statement=text[start:statement_end], reference_proof=proof,
                proof_start=proof_start, proof_end=proof_end, source_sha256=sha(text),
                proof_lines=nonempty, reference_token_count=len(score.tokenize_proof_body(proof))))
    return sorted(candidates, key=lambda r: (r['proof_lines'], r['source_file'], r['theorem_name'])), sorted(excluded_files)


def mine(repo, upstream, warmups, output, count=10):
    from .verification import verify
    output = Path(output)
    if output.exists(): raise ValueError('Mining output already exists; use a new run directory')
    candidates, excluded = inventory(repo, upstream, warmups)
    jsonl(output / 'inventory.jsonl', candidates)
    save(output / 'exclusions.json', dict(files=excluded, warmup_sha256={str(p): sha(read(p)) for p in warmups}))
    selected, failures = [], []
    for row in candidates:
        result = verify(repo, row, row['reference_proof'], output / 'references' / row['problem_id'])
        if result['compile_success'] and result['safety_passed']:
            row['reference_verification'] = result
            selected.append(row)
            text = git(repo, 'show', f"{row['source_commit']}:{row['source_file']}")
            write(output / 'sources' / row['source_file'], text)
            print('Verified', row['theorem_name'], row['proof_lines'], flush=True)
        else:
            failures.append(dict(theorem_name=row['theorem_name'], result=result))
            print('Rejected reference', row['theorem_name'], result['error_category'], flush=True)
        if len(selected) == count: break
    jsonl(output / 'theorems.jsonl', selected)
    save(output / 'mining.json', dict(requested=count, selected=len(selected), eligible=len(candidates),
                                     rejected=failures, minimum_nonempty_proof_lines=31))
    if len(selected) < count: raise RuntimeError(f'Shortage: {len(selected)} verified theorems / {count}')
