"""Export Arena upload JSONL; does not submit or claim official proof validity.

The intake filter below is taken from the official Space app at RULES_REVISION.
The statement/declaration and manifest checks are additional local safeguards.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RULES_REVISION = "8fdaaaa25b993ae8d894e9bb756c3ae222b58507"
RULES_URL = f"https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/blob/{RULES_REVISION}/app.py"

_FORBIDDEN_PATTERNS: list[tuple[str, "re.Pattern[str]"]] = [
    ("#eval", re.compile(r"#\s*eval\b")),
    ("#reduce", re.compile(r"#\s*reduce\b")),
    ("IO.", re.compile(r"\bIO\.")),
    ("unsafe def/fun/theorem", re.compile(r"\bunsafe\s+(def|fun|theorem|lemma)\b")),
    ("extern", re.compile(r"\bextern\b")),
    ("initialize", re.compile(r"\binitialize\b")),
    ("@[implemented_by]", re.compile(r"@\[\s*implemented[_]?[Bb]y\b")),
    ("@[extern]", re.compile(r"@\[\s*extern\b")),
    ("sorry", re.compile(r"\bsorry\b")),
    ("sorryAx", re.compile(r"\bsorryAx\b")),
    ("admit", re.compile(r"\badmit\b")),
    ("axiom", re.compile(r"\baxiom\b")),
    ("native_decide", re.compile(r"\bnative_decide\b")),
    ("ofReduceBool", re.compile(r"\bofReduceBool\b")),
    ("ofReduceNat", re.compile(r"\bofReduceNat\b")),
    ("run_cmd", re.compile(r"\brun_cmd\b")),
    ("run_elab", re.compile(r"\brun_elab\b")),
    ("#exit", re.compile(r"#\s*exit\b")),
    ("#count_heartbeats", re.compile(r"#\s*count_heartbeats\b")),
    ("attribute command", re.compile(r"(?m)^\s*attribute\b")),
    ("macro/elab/notation", re.compile(
        r"\b(macro|macro_rules|elab|elab_rules|notation|syntax)\b")),
    ("deriving instance", re.compile(r"\bderiving\s+instance\b")),
    ("auxiliary declaration", re.compile(
        r"(?m)^\s*(def|abbrev|instance|structure|inductive|class|opaque)\b")),
]

_MAX_PROOF_BYTES = 256 * 1024

def _strip_lean_comments(text: str) -> str:
    """Drop `/- … -/` blocks (nested) and `--` line tails so comments can't
    trip the forbidden-pattern check. String-literal aware and a single O(n)
    scan — a regex here (`/-.*?-/`) both misses string-embedded delimiters
    (letting a proof hide `#eval` between two string literals) and goes
    quadratic on adversarial `/-` repetition. Mirrors the worker's
    `lra.lean_utils.remove_comments` scanner."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            out.append(c)
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == "\\" and i + 1 < n:
                    out.append(text[i + 1])
                    i += 2
                    continue
                if text[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if text.startswith("/-", i):
            depth, i = 1, i + 2
            while i < n and depth:
                if text.startswith("/-", i):
                    depth += 1
                    i += 2
                elif text.startswith("-/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            out.append(" ")
            continue
        if text.startswith("--", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)

def _check_forbidden(code: str) -> str | None:
    if len(code) > _MAX_PROOF_BYTES:
        return f"too large (> {_MAX_PROOF_BYTES // 1024} KB)"
    stripped = _strip_lean_comments(code)
    for label, pat in _FORBIDDEN_PATTERNS:
        if pat.search(stripped):
            return label
    return None


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_proof(proof, benchmark):
    violation = _check_forbidden(proof)
    if violation:
        raise ValueError(f"{benchmark['name']}: forbidden pattern: {violation}")
    statement = benchmark['statement']
    if not proof.startswith(statement):
        raise ValueError(f"{benchmark['name']}: expected the exact benchmark statement at the start; no helper declarations before it")
    rest = proof[len(statement):]
    if not re.match(r"\s*:=\s*\S", rest):
        raise ValueError(f"{benchmark['name']}: missing proof body after :=")
    # The official upload regex does not reject extra lemma/theorem commands,
    # but the written rules require just the benchmark declaration and its proof.
    body = _strip_lean_comments(rest)
    if re.search(r"\b(theorem|lemma|example)\b", body) or re.search(
        r"(?m)^\s*(?:(?:private|protected|noncomputable)\s+)*"
        r"(?:def|abbrev|instance|structure|inductive|class|opaque|import|namespace|"
        r"section|end|variable|universe|export)\b", body
    ):
        raise ValueError(f"{benchmark['name']}: additional declaration in proof")


def build_bundle(root=ROOT, *, p12_reference=False):
    folder = root / 'submissions/warmup'
    manifest = json.loads((folder / 'manifest.json').read_text())
    benchmark_path = root / manifest['benchmarkSnapshot']
    benchmark_bytes = benchmark_path.read_bytes()
    benchmark = [json.loads(line) for line in benchmark_bytes.decode().splitlines() if line.strip()]
    by_name = {row['name']: row for row in benchmark}
    if len(benchmark) != 15 or len(by_name) != 15:
        raise ValueError('Expected exactly 15 unique warmup benchmark names')
    rows, evidence = [], []
    for entry in manifest['problems']:
        name = entry['name']
        if name not in by_name:
            raise ValueError(f'Unknown benchmark name: {name}')
        path = folder / entry['path']
        data = path.read_bytes()
        if sha(data) != entry['sha256']:
            raise ValueError(f'Best proof hash differs from manifest: {path}')
        fallback = entry['id'] == 12 and p12_reference
        proof = by_name[name]['src'] if fallback else data.decode('utf-8')
        validate_proof(proof, by_name[name])
        rows.append({'name': name, 'proof': proof})
        evidence.append({
            'id': entry['id'], 'name': name,
            'selection': 'official_reference_fallback' if fallback else 'team_best',
            'source': manifest['benchmarkSnapshot'] if fallback else str(path.relative_to(root)),
            'sha256': sha(proof.encode()), 'teamBestSha256': entry['sha256'],
            'localStatus': 'reference_not_reverified' if fallback else entry['status'],
            'versions': entry['versions'],
            'note': ('P12 team candidate has three top-level helper lemmas. The upload uses the unchanged official reference until that candidate is repaired and verified.' if fallback else ''),
        })
    if len(rows) != 15 or {r['name'] for r in rows} != set(by_name):
        raise ValueError('Expected exactly one row for every warmup problem')
    payload = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows).encode()
    if len(payload) > 8 * 1024 * 1024:
        raise ValueError('Submission exceeds the official 8 MiB intake limit')
    audit = {
        'schemaVersion': 1, 'rulesRevision': RULES_REVISION, 'rulesSource': RULES_URL,
        'benchmarkRevision': manifest['benchmarkRevision'],
        'benchmarkSha256': sha(benchmark_bytes), 'submissionSha256': sha(payload),
        'format': 'UTF-8 JSONL; one name/proof object per line', 'rows': len(rows),
        'checks': {'uniqueOfficialNames': True, 'exactStatements': True,
                   'officialIntakePatternCheck': True, 'singleDeclarationCheck': True,
                   'sourceHashes': True},
        'officiallySubmitted': False, 'officialEvaluationPassed': None,
        'apiEligibility': manifest['apiEligibility'],
        'limitations': [
            'Packaging checks are not Lean compilation or official scoring.',
            'P03, P07, P08, P09 still have pending designated-version checks.',
            'No exemption from the OpenRouter, budget or reproduction requirements is inferred from warmup upload availability.',
        ],
        'problems': evidence,
    }
    if p12_reference:
        audit['limitations'].append('P12 uses the official reference, not the owner refactor; it has not been reverified in this export.')
    return payload, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--p12-reference', action='store_true', help='Explicitly use the official P12 reference instead of its unsupported team refactor')
    parser.add_argument('--output', type=Path, default=ROOT / 'submissions/warmup/submission.jsonl')
    args = parser.parse_args()
    payload, audit = build_bundle(p12_reference=args.p12_reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    audit_path = args.output.with_suffix('.audit.json')
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    print(f'{args.output}: {len(payload)} bytes, {audit["rows"]} rows')
    print(f'Audit: {audit_path}')


if __name__ == '__main__':
    main()
