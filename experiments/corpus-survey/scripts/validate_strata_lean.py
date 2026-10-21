#!/usr/bin/env python3
"""Build original Strata modules and join source declarations to kernel axiom evidence.

Run after sourcing the project env/use.sh. Build output stays in Strata's central
.lake symlink. This validates original source modules, not rewritten proof tasks.
Lean's declaration-range extension selects exact constants, including private
names; the axiom collector walks their compiled proof terms transitively.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


from arena_workspace import ROOT
PIN = "451e5f047bafa010d178856db76c00029bfa4d7f"


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
    parser.add_argument("--source-root", type=Path, default=ROOT / "sources/strata")
    parser.add_argument("--inventory", type=Path, default=ROOT / "strata/inventory.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "strata/validation")
    parser.add_argument("--lake", default=str(Path.home() / ".elan/bin/lake"))
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
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
        raise SystemExit("Strata .lake must symlink to the centralized project cache")
    start = time.monotonic()
    build_cmd = [args.lake, "build", *modules]
    with (output / "build.log").open("w") as log:
        built = subprocess.run(build_cmd, cwd=source_root, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
    if built.returncode:
        raise SystemExit(f"Module build failed; see {output / 'build.log'}")
    axiom_cmd = [args.lake, "env", "lean", "--run", str(ROOT / "scripts/InspectStrataAxioms.lean"), *modules]
    with (output / "kernel_constants.jsonl").open("w") as log:
        checked = subprocess.run(axiom_cmd, cwd=source_root, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
    if checked.returncode:
        raise SystemExit(f"Kernel inspection failed; see {output / 'kernel_constants.jsonl'}")
    constants = jsonl(output / "kernel_constants.jsonl")
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
                "module_build_passed": True, "mapping_method": "kernel_selection_range_in_declaration_byte_range"}
        if "id" in row:
            item["id"] = row["id"]
        if len(matches) == 1:
            native = matches[0]
            item.update(native)
            item["kernel_mapping_status"] = "unique"
            item["original_proof_axioms_checked"] = True
        else:
            item["kernel_mapping_status"] = "missing" if not matches else "ambiguous"
            item["original_proof_axioms_checked"] = False
            item["candidates"] = [native["kernel_name"] for native in matches]
        validations.append(item)
    dump_jsonl(output / "declarations.jsonl", validations)
    mapped = [v for v in validations if v["original_proof_axioms_checked"]]
    summary = {"source_revision": revision, "lean_toolchain": (source_root / "lean-toolchain").read_text().strip(),
               "inventory_sha256": hashlib.sha256(args.inventory.read_bytes()).hexdigest(),
               "inventory_count": len(rows), "modules_built": len(modules),
               "module_build_passed": True, "mapped_declarations": len(mapped),
               "with_transitive_sorryAx": sum(v["has_sorryAx"] for v in mapped),
               "without_transitive_sorryAx": sum(not v["has_sorryAx"] for v in mapped),
               "scope": "Original source modules compiled; selected kernel theorem proof terms inspected transitively. No rewritten proof validation.",
               "build_command": build_cmd, "axiom_command": axiom_cmd,
               "seconds": round(time.monotonic() - start, 3), "files": sources}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("files", "build_command", "axiom_command")}, indent=2))
    return 0 if len(mapped) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
