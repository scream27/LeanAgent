#!/usr/bin/env python3
"""Sequential native PhysLib parser audit, retaining every input and failed attempt.

Source-import environments are isolated in ONE Lean subprocess per file because
repeated imports in a long-lived Lean process can retain substantial memory.
This script never builds dependencies and never starts concurrent parser jobs.
Use --max-files for a bounded run; --merge-only performs no Lean execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from physlib_lexical import declaration_positions
from run_physlib_bounded import run_bounded

from arena_workspace import ROOT
HELPER = ROOT / "scripts/ExtractPhyslibDeclarations.lean"
CACHE = Path(os.environ.get("PROJECT_CACHE_DIR", "/Users/jwkweon/00_work/00_project/cache/05_pseudolab/LeanAgent-LeanRefactorArena")) / "physlib-extract"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def atomic_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(path)


def relative_path(row: dict, repo: Path) -> str:
    path = Path(row.get("file_path", row.get("path", "")))
    return str(path.relative_to(repo)) if path.is_absolute() else path.as_posix()


def quality(row: dict, data: bytes) -> tuple[int, int, int]:
    """Favor coverage of real lexical keywords; retain raw recovery nodes in audit."""
    text = data.decode()
    expected = {len(text[:char].encode()) for char in declaration_positions(text)}
    complete = set()
    found = set()
    for node in row.get("declarations", []):
        start = (node.get("declaration_range") or {}).get("start_byte")
        if start in expected:
            found.add(start)
            if not node.get("has_missing_syntax") and node.get("value_range"):
                complete.add(start)
    return len(complete), len(found), -len(row.get("errors", []))


def run_guarded(command: list[str], repo: Path, env: dict, timeout: int, max_rss_mb: int) -> dict:
    """Use the shared, tested process-group watchdog and preserve each source log."""
    log = CACHE / "logs" / (sha(command[-1].encode())[:16] + ".log")
    report = run_bounded(command, cwd=repo, log=log, env=env,
                         timeout=timeout, max_rss_mb=max_rss_mb)
    output = log.read_text()
    return {"returncode": report["returncode"], "stdout": output,
            "stderr": "\n".join(line for line in output.splitlines() if not line.startswith("{")),
            "resource_stop": report["stop_reason"], "peak_rss_mb": report["peak_group_rss_mb"],
            "log": str(log)}


def normalized(row: dict, data: bytes, path: str) -> dict:
    text = data.decode()
    expected = {len(text[:char].encode()) for char in declaration_positions(text)}
    declarations = {}
    recovery = list(row.get("recovery_nodes", []))
    for node in row.get("declarations", []):
        start = (node.get("declaration_range") or {}).get("start_byte")
        if start not in expected:
            recovery.append(dict(node, recovery_reason="not_a_source_declaration_keyword"))
        elif start in declarations:
            old = declarations[start]
            if old.get("has_missing_syntax") and not node.get("has_missing_syntax"):
                recovery.append(dict(old, recovery_reason="duplicate_recovered_declaration"))
                declarations[start] = node
            else:
                recovery.append(dict(node, recovery_reason="duplicate_recovered_declaration"))
        else:
            declarations[start] = node
    return dict(row, path=path, file_path=path, file_sha256=sha(data),
                declarations=list(declarations.values()), recovery_nodes=recovery)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT / "sources/physlib")
    parser.add_argument("--output", type=Path, default=CACHE / "all.jsonl")
    parser.add_argument("--baseline", type=Path, default=CACHE / "all-broad.jsonl")
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--max-rss-mb", type=int, default=1536)
    parser.add_argument("--lean-memory-mb", type=int, default=1024)
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--retry-failed", action="store_true", help="Retry cached failed source imports after dependencies change")
    parser.add_argument("--all-files", action="store_true", help="Also reparse baseline files without parser errors")
    args = parser.parse_args()
    repo = args.repo.resolve()
    toolchain = (repo / "lean-toolchain").read_text().strip()
    executable = Path(os.environ.get("PHYSLIB_LEAN_BIN", str(Path.home() / ".elan/toolchains" / toolchain.replace("/", "--").replace(":", "---") / "bin/lean")))
    if not executable.exists():
        raise SystemExit(f"Pinned Lean executable unavailable: {executable}")
    files = [p for p in subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z", "*.lean"]).decode().split("\0") if p]
    source_data = {p: (repo / p).read_bytes() for p in files}
    baseline = {relative_path(row, repo): row for row in load(args.baseline)}
    attempt_file = CACHE / "source-attempts.jsonl"
    helper_hash = sha(HELPER.read_bytes())
    cached = {}
    for row in load(attempt_file):
        path = row.get("file_path")
        if path in source_data and row.get("file_sha256") == sha(source_data[path]) and row.get("helper_sha256") == helper_hash:
            cached[path] = row
    attempted = 0
    resource_stopped = False
    results = [normalized(baseline.get(path, {"fatal_error": "No completed baseline audit"}), source_data[path], path) for path in files]
    atomic_jsonl(args.output, results)
    CACHE.mkdir(parents=True, exist_ok=True)
    for index, path in enumerate(files):
        data = source_data[path]
        base = baseline.get(path, {"path": path, "fatal_error": "No completed baseline audit", "declarations": [], "commands": [], "errors": []})
        old_hash = base.get("file_sha256")
        if old_hash is not None and old_hash != sha(data):
            base = {"path": path, "fatal_error": "Baseline source hash mismatch", "declarations": [], "commands": [], "errors": []}
        attempt = cached.get(path)
        if args.retry_failed and attempt and attempt["audit"].get("fatal_error"):
            attempt = None
        needs_retry = args.all_files or bool(base.get("fatal_error") or base.get("errors")) or any(n.get("has_missing_syntax") for n in base.get("declarations", []))
        allowed = not resource_stopped and not args.merge_only and (args.max_files is None or attempted < args.max_files)
        if attempt is None and needs_retry and allowed:
            attempted += 1
            command = [str(executable.with_name("lake")), "env", str(executable), f"-M{args.lean_memory_mb}", "--run", str(HELPER), "--source-imports", "--local-syntax", "--syntax-module=Mathlib.Tactic.Lemma", path]
            env = dict(os.environ, LEAN_NUM_THREADS="1")
            print(f"[{index + 1}/{len(files)}] Native source-import audit: {path}", file=sys.stderr, flush=True)
            proc = run_guarded(command, repo, env, args.timeout, args.max_rss_mb)
            native_rows = []
            for line in proc["stdout"].splitlines():
                if line.startswith("{"):
                    try:
                        native_rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            native = native_rows[-1] if native_rows else {"path": path, "fatal_error": proc["resource_stop"] or "Native process produced no audit"}
            attempt = {"file_path": path, "file_sha256": sha(data), "helper_sha256": helper_hash,
                       "returncode": proc["returncode"], "stderr": proc["stderr"][-8000:], "audit": native,
                       "resource_stop": proc["resource_stop"], "peak_rss_mb": proc["peak_rss_mb"], "log": proc["log"]}
            resource_stopped = bool(proc["resource_stop"] or proc["returncode"] < 0 or proc["returncode"] in (137, 139) or any(message in (proc["stderr"] + proc["stdout"]).lower() for message in ("out of memory", "maximum memory", "memory limit")))
            with attempt_file.open("a") as stream:
                stream.write(json.dumps(attempt, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        selected = base
        if attempt and not attempt["audit"].get("fatal_error") and quality(attempt["audit"], data) >= quality(base, data):
            selected = attempt["audit"]
        result = normalized(selected, data, path)
        result["source_import_attempt"] = ({k: v for k, v in attempt.items() if k != "audit"} | {
            "audit_journal": str(attempt_file), "fatal_error": attempt["audit"].get("fatal_error")}) if attempt is not None else {"status": "not_attempted"}
        results[index] = result
        if attempt is not None:
            atomic_jsonl(args.output, results)
    # A partial/bounded run still has one explicit audit (or fatal placeholder) per tracked file.
    atomic_jsonl(args.output, results)
    print(json.dumps({"output": str(args.output), "files": len(results), "native_attempts_this_run": attempted, "resource_stopped": resource_stopped, "fatal_files": sum(bool(row.get("fatal_error")) for row in results)}))


if __name__ == "__main__":
    main()
