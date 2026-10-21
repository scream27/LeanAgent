#!/usr/bin/env python3
"""Reproducible, lexical pilot survey. No Lean code from upstream is executed."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

from arena_workspace import ROOT
ARENA = "https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena"
DEFAULT_REV = "56aa7b8f738d1d6a0a24a55e03cdea1a84007b6c"
STRATA_REV = "451e5f047bafa010d178856db76c00029bfa4d7f"
TACTICS = set("""intro intros rintro exact exact? apply apply? refine constructor
  left right exists use obtain rcases cases induction rename_i case next have
  suffices show change simpa simp simp_all dsimp unfold rw rwa simp_rw
  aesop grind omega linarith nlinarith ring ring_nf norm_num positivity
  field_simp decide native_decide rfl refl assumption contradiction
  by_cases by_contra exfalso push_neg ext funext congr congrArg gcongr
  subst specialize generalize revert clear trivial tauto finish
  split split_ifs injections injection simp? aesop? norm_cast exact_mod_cast
  convert calc classical infer_instance
""".split())
COMBINATORS = {"try", "repeat", "repeat'", "first", "all_goals", "any_goals", "focus"}
TOKEN = re.compile(r"<;>|=>|[\w][\w'.?!]*|[^\s]", re.UNICODE)


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mask_noncode(source: str) -> str:
    """Mask nested comments and strings, retaining offsets and newlines.

    This is not a Lean parser. Syntax quotations and term/tactic ambiguity remain.
    Raw strings, escaped strings, and simple/escaped character literals are masked.
    """
    out = list(source)
    i, n = 0, len(source)

    def blank(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        start = i
        if source.startswith("--", i):
            end = source.find("\n", i)
            i = n if end < 0 else end
        elif source.startswith("/-", i):
            depth = 1
            i += 2
            while i < n and depth:
                if source.startswith("/-", i):
                    depth += 1
                    i += 2
                elif source.startswith("-/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
        elif (raw := re.match(r'r(#+)"', source[i:])) and (i == 0 or not source[i-1].isalnum()):
            close = '"' + raw[1]
            end = source.find(close, i + len(raw[0]))
            i = n if end < 0 else end + len(close)
        elif source[i] == '"':
            i += 1
            while i < n:
                if source[i] == "\\":
                    i = min(n, i + 2)
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
        elif source[i] == "'" and (i == 0 or not re.match(r"[\w']", source[i-1])) and (char := re.match(r"'(?:\\.|[^'\n])'", source[i:])):
            i += len(char[0])
        else:
            i += 1
            continue
        blank(start, i)
    return "".join(out)


def tactic_heads(source: str) -> list[dict]:
    """Count allowlisted heads at likely tactic boundaries, not executions.

    `<;> simp` is one syntactic occurrence even if it runs over many goals.
    `have`, `show`, `calc`, etc. may also occur in term syntax. Unknown/custom
    tactics are not counted. Inline syntax quotations may produce false positives.
    """
    masked = mask_noncode(source)
    hits = []
    previous, last_end, line, last_pos = None, 0, 1, 0
    for match in TOKEN.finditer(masked):
        word = match[0]
        gap = masked[last_end:match.start()]
        line += masked[last_pos:match.start()].count("\n")
        boundary = previous is None or "\n" in gap or previous in {"by", ";", "<;>", "=>", "|", "·", ".", "(", *COMBINATORS}
        if boundary and word in TACTICS:
            hit = {"tactic": word, "line": line}
            if word == "simp":
                hit["form"] = "simp only" if re.match(r"\s+only\b", masked[match.end():]) else "simp other"
            hits.append(hit)
        previous, last_end, last_pos = word, match.end(), match.start()
    return hits


def counts(source: str) -> dict:
    return dict(Counter(x["tactic"] for x in tactic_heads(source)).most_common())


def fetch(revision: str):
    folder = ROOT / "data/arena" / revision
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in ["benchmark_data_warmup.jsonl", "benchmark_heartbeats.jsonl", "benchmark.py", "app.py"]:
        url = f"{ARENA}/resolve/{revision}/{name}"
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        (folder / name).write_bytes(data)
        files[name] = {"url": url, "sha256": digest(data), "bytes": len(data)}
    tree = ast.parse((folder / "benchmark.py").read_text())
    sources = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                   and node.target.id == "SOURCES")
    manifest = {"arena_revision": revision, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "files": files, "sources": sources}
    dump(ROOT / "data/arena_snapshot.json", manifest)
    print(f"Pinned Arena snapshot: {revision}; {len(sources)} sources")


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def survey(repo: Path, revision: str):
    snapshot = json.loads((ROOT / "data/arena_snapshot.json").read_text())
    arena = ROOT / "data/arena" / snapshot["arena_revision"]
    for name, metadata in snapshot["files"].items():
        if digest((arena / name).read_bytes()) != metadata["sha256"]:
            raise ValueError(f"Arena snapshot changed: {name}")
    problems = [json.loads(line) for line in (arena / "benchmark_data_warmup.jsonl").read_text().splitlines() if line.strip()]
    heartbeats = {r["name"]: r["heartbeat"] for r in
                  map(json.loads, (arena / "benchmark_heartbeats.jsonl").read_text().splitlines())}
    revision = git(repo, "rev-parse", f"{revision}^{{commit}}").decode().strip()
    warmup = []
    for number, problem in enumerate(problems, 1):
        # src may have preceding open/omit commands; statement is the exact anchor.
        statement_start = problem["src"].find(problem["statement"])
        if statement_start < 0:
            raise ValueError(f"Statement not present in P{number}")
        body = problem["src"][statement_start + len(problem["statement"]):].lstrip()
        if not body.startswith(":="):
            raise ValueError(f"No proof delimiter in P{number}")
        body = body[2:]
        record = {"number": number, "name": problem["name"], "source": problem["source"],
                  "official_proof_length": problem["proof_length"],
                  "official_reference_heartbeat": heartbeats.get(problem["name"]),
                  "heartbeat_status": "published_reference_not_locally_measured",
                  "version_info": problem["version_info"],
                  "file_path": problem["file_path"], "src_sha256": digest(problem["src"].encode()),
                  "approximate_tactic_heads": counts(body)}
        if problem["source"] == "strata":
            text = git(repo, "show", f"{revision}:{problem['file_path']}").decode()
            span = "\n".join(text.splitlines()[problem["start_line"]-1:problem["end_line"]])
            record["line_span_matches_at_pilot_revision"] = span.strip() == problem["src"].strip()
            record["src_present_at_pilot_revision"] = problem["src"].strip() in text
            source = problem["src"].strip()
            record["src_match_count_at_pilot_revision"] = text.count(source)
            if text.count(source) == 1:
                start = text.index(source)
                record["located_lines_at_pilot_revision"] = [text[:start].count("\n") + 1,
                    text[:start + len(source)].count("\n") + 1]
        warmup.append(record)
        path = ROOT / f"artifacts/warmup/P{number:02d}.lean"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(problem["src"])
    files = []
    total, production = Counter(), Counter()
    for raw in git(repo, "ls-tree", "-r", "--name-only", "-z", revision).split(b"\0"):
        if not raw or not raw.endswith(b".lean"):
            continue
        path = raw.decode()
        data = git(repo, "show", f"{revision}:{path}")
        text = data.decode()
        hits = tactic_heads(text)
        counter = Counter(x["tactic"] for x in hits)
        group = "library" if path.startswith("Strata/") else "tests" if path.startswith("StrataTest") else "other"
        total.update(counter)
        if group == "library":
            production.update(counter)
        item = {"path": path, "group": group, "sha256": digest(data), "lines": len(text.splitlines()),
                "approximate_tactic_heads": dict(counter.most_common()), "occurrences": hits,
                "quotation_or_metaprogramming_risk": bool(re.search(r"`\(|\b(?:macro|elab|syntax)\b", mask_noncode(text)))}
        files.append(item)
        extracted = ROOT / "artifacts/strata" / revision / path
        extracted.parent.mkdir(parents=True, exist_ok=True)
        extracted.write_bytes(data)
    summary = {"method": "lexical-heads-v1", "script_sha256": digest(Path(__file__).read_bytes()),
               "arena_revision": snapshot["arena_revision"], "strata_revision": revision,
               "lean_toolchain": git(repo, "show", f"{revision}:lean-toolchain").decode().strip(),
               "warmup_distribution": dict(Counter(x["source"] for x in problems)),
               "lean_files": len(files), "files_by_group": dict(Counter(f["group"] for f in files)),
               "all_approximate_tactic_heads": dict(total.most_common()),
               "library_approximate_tactic_heads": dict(production.most_common()),
               "library_simp_forms": dict(Counter(h["form"] for f in files if f["group"] == "library"
                                                   for h in f["occurrences"] if "form" in h)),
               "limitations": ["Not a Lean parser or dynamic execution count; fixed allowlist, possible false positives and misses.",
                               "have/show/calc etc. include term syntax; syntax quotations may include tactic examples.",
                               "No local heartbeat measurements. Published heartbeats have no per-tactic attribution.",
                               "One historical Strata snapshot; not the unreleased full benchmark or all versions."]}
    dump(ROOT / "results/summary.json", summary)
    dump(ROOT / "results/warmup.json", warmup)
    dump(ROOT / "results/strata_files.json", files)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    download = sub.add_parser("fetch")
    download.add_argument("--revision", default=DEFAULT_REV)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--repo", type=Path, default=ROOT / "sources/strata")
    analyze.add_argument("--revision", default=STRATA_REV)
    args = parser.parse_args()
    if args.command == "fetch":
        fetch(args.revision)
    else:
        survey(args.repo, args.revision)


if __name__ == "__main__":
    main()
