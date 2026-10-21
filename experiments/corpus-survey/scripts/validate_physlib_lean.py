#!/usr/bin/env python3
"""Build original Physlib modules independently and join source declarations to kernel axiom evidence.

Run after sourcing the project env/use.sh. Build output stays in Physlib's central
.lake symlink. This validates original source modules, not rewritten proof tasks.
Lean's declaration-range extension selects exact constants, including private
names; the axiom collector walks their compiled proof terms transitively.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from run_physlib_bounded import run_bounded


from arena_workspace import ROOT
PIN = "c48433678e8fb6306ebcd48453300c8e16058a62"


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def dump_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def source_position_byte(source, line, column):
    """Lean Position uses one-based lines and zero-based Unicode columns."""
    lines = source.splitlines(keepends=True)
    prefix = "".join(lines[:line - 1])
    text = lines[line - 1][:column]
    return len((prefix + text).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "sources/physlib")
    parser.add_argument("--inventory", type=Path, default=ROOT / "physlib/inventory.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "physlib/validation")
    parser.add_argument("--lake", default=str(Path.home() / ".elan/bin/lake"))
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    os.environ["LEAN_NUM_THREADS"] = "2"
    source_root = args.source_root.resolve()
    rows = jsonl(args.inventory)
    files = sorted({row["file_path"] for row in rows})
    modules = [str(Path(path).with_suffix("")).replace("/", ".") for path in files]
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True).strip()
    if revision != PIN:
        raise SystemExit(f"Unexpected source revision {revision}")
    dirty = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=source_root, text=True).strip()
    if dirty:
        raise SystemExit(f"Tracked source changes prevent pinned validation: {dirty}")
    lake_dir = source_root / ".lake"
    cache_root = Path("/Users/jwkweon/00_work/00_project/cache")
    if not lake_dir.is_symlink() or cache_root not in lake_dir.resolve().parents:
        raise SystemExit("Physlib .lake must symlink to the centralized project cache")
    start = time.monotonic()
    build_cmd = [args.lake, "build", *modules]
    with (output / "build.log").open("w") as log:
        built = subprocess.run(build_cmd, cwd=source_root, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
    # A pinned source can itself be broken. Probe each target without permitting
    # further builds; this verifies a current Lake artifact, not just file presence.
    module_logs = output / "modules"
    module_logs.mkdir(exist_ok=True)
    def probe(module):
        cmd = [args.lake, "--no-build", "build", module]
        result = subprocess.run(cmd, cwd=source_root, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=args.timeout)
        log_name = module + ".log"
        (module_logs / log_name).write_text(result.stdout)
        return module, {"module": module, "module_build_passed": result.returncode == 0,
                        "build_probe_returncode": result.returncode, "build_probe_command": cmd,
                        "build_log": "modules/" + log_name}
    with ThreadPoolExecutor(max_workers=1) as pool:
        statuses = dict(pool.map(probe, modules))
    successful = [m for m in modules if statuses[m]["module_build_passed"]]
    constants = []
    axiom_commands = []
    inspect_logs = output / "inspection"
    inspect_logs.mkdir(exist_ok=True)
    # A shared import is faster and yields exact ranges even for private constants.
    # Recursively isolate a module if a batch cannot be imported/inspected.
    def inspect(batch, label):
        cmd = [args.lake, "env", "lean", "--run",
               str(ROOT / "scripts/InspectPhyslibAxioms.lean"), *batch]
        axiom_commands.append(cmd)
        result = subprocess.run(cmd, cwd=source_root, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, timeout=args.timeout)
        (inspect_logs / (label + ".stderr.log")).write_text(result.stderr)
        (inspect_logs / (label + ".jsonl")).write_text(result.stdout)
        if result.returncode:
            if len(batch) > 1:
                middle = len(batch) // 2
                inspect(batch[:middle], label + "a")
                inspect(batch[middle:], label + "b")
            else:
                statuses[batch[0]]["kernel_inspection_passed"] = False
                statuses[batch[0]]["inspection_log"] = "inspection/" + label + ".stderr.log"
            return
        constants.extend(json.loads(line) for line in result.stdout.splitlines() if line.strip())
        for module in batch:
            statuses[module]["kernel_inspection_passed"] = True
    for start_index in range(0, len(successful), 48):
        inspect(successful[start_index:start_index + 48], f"batch-{start_index:04d}")
    dump_jsonl(output / "kernel_constants.jsonl", sorted(constants, key=lambda x: (x["module"], x["kernel_name"])))
    dump_jsonl(output / "modules.jsonl", [statuses[m] for m in modules])
    locations = {}
    sources = {}
    for file_path, module in zip(files, modules):
        raw = (source_root / file_path).read_bytes()
        source = raw.decode("utf-8")
        sources[file_path] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "module": module}
        entries = []
        for native in constants:
            selection = native["selection_range"]
            if native["module"] == module and selection is not None:
                position = source_position_byte(source, selection["start_line"], selection["start_column"])
                entries.append((position, native))
        locations[file_path] = entries
    validations = []
    for row in rows:
        file_path = row["file_path"]
        if row.get("file_sha256", sources[file_path]["sha256"]) != sources[file_path]["sha256"]:
            raise SystemExit(f"Inventory source hash mismatch: {file_path}")
        matches = [native for offset, native in locations[file_path]
                   if row["start_byte"] <= offset < row["end_byte"]]
        # Generated mutual/_unary helpers can share source ranges. Exact native
        # user names disambiguate only constants already verified at that range.
        if len(matches) > 1:
            exact = [native for native in matches if native["user_name"] == row["name"]]
            if len(exact) == 1:
                matches = exact
        item = {"name": row["name"], "file_path": file_path,
                "start_byte": row["start_byte"], "end_byte": row["end_byte"],
                "source_sha256": sources[file_path]["sha256"],
                "module_build_passed": statuses[sources[file_path]["module"]]["module_build_passed"], "mapping_method": "kernel_selection_range_in_declaration_byte_range"}
        if "id" in row:
            item["id"] = row["id"]
        module_status = statuses[sources[file_path]["module"]]
        if not module_status["module_build_passed"]:
            item["kernel_mapping_status"] = "module_build_failed"
            item["original_proof_axioms_checked"] = False
            item["build_log"] = module_status["build_log"]
            item["failure_reason"] = "Original pinned module failed compilation or has an unavailable dependency; see build.log and module probe log."
        elif not module_status.get("kernel_inspection_passed", False):
            item["kernel_mapping_status"] = "kernel_inspection_failed"
            item["original_proof_axioms_checked"] = False
        elif len(matches) == 1 and matches[0]["user_name"] == row["name"]:
            native = matches[0]
            item.update(native)
            item["kernel_mapping_status"] = "unique"
            item["original_proof_axioms_checked"] = True
        else:
            item["kernel_mapping_status"] = ("missing" if not matches else
                                             "name_mismatch" if len(matches) == 1 else "ambiguous")
            item["original_proof_axioms_checked"] = False
            item["candidates"] = [native["kernel_name"] for native in matches]
        validations.append(item)
    mapped_keys = [(v["module"], v["kernel_name"]) for v in validations
                   if v["original_proof_axioms_checked"]]
    if len(mapped_keys) != len(set(mapped_keys)):
        raise SystemExit("Multiple inventory declarations mapped to the same kernel constant")
    dump_jsonl(output / "declarations.jsonl", validations)
    mapped = [v for v in validations if v["original_proof_axioms_checked"]]
    summary = {"source_revision": revision, "lean_toolchain": (source_root / "lean-toolchain").read_text().strip(),
               "inventory_sha256": hashlib.sha256(args.inventory.read_bytes()).hexdigest(),
               "inventory_count": len(rows), "modules_requested": len(modules),
               "modules_built": len(successful), "modules_failed": len(modules) - len(successful),
               "module_build_passed": built.returncode == 0,
               "build_returncode": built.returncode,
               "lean_version": subprocess.check_output([args.lake, "env", "lean", "--version"], cwd=source_root, text=True).strip(),
               "unverified_declarations": len(rows) - len(mapped), "mapped_declarations": len(mapped),
               "with_transitive_sorryAx": sum(v["has_sorryAx"] for v in mapped),
               "without_transitive_sorryAx": sum(not v["has_sorryAx"] for v in mapped),
               "environment": {"LEAN_NUM_THREADS": "2"},
               "mapping_checks": ["selection_range_inside_declaration", "exact_user_name", "globally_unique_kernel_constant"],
               "scope": "Original source modules requested for compilation; successful targets and selected kernel theorem proof terms inspected transitively. Failed targets retain explicit unavailable statuses. No rewritten proof validation.",
               "build_command": build_cmd, "axiom_commands": axiom_commands,
               "seconds": round(time.monotonic() - start, 3), "files": sources}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("files", "build_command", "axiom_commands")}, indent=2))
    return 0 if len(mapped) == len(rows) else 1


if __name__ == "__main__":
    if "--bounded-child" in sys.argv:
        sys.argv.remove("--bounded-child")
        os.environ["LEAN_NUM_THREADS"] = "1"
        raise SystemExit(main())
    report = run_bounded([sys.executable, str(Path(__file__).resolve()), "--bounded-child", *sys.argv[1:]],
                         cwd=ROOT, log=ROOT / "physlib/validation/bounded-validation.log",
                         max_rss_mb=1536, timeout=7200)
    print(json.dumps(report, indent=2))
    raise SystemExit(125 if report["stop_reason"] else report["returncode"])
