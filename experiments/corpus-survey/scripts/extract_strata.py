#!/usr/bin/env python3
"""Extract refactorable declarations using Lean's pinned native syntax parser.

The source is immutable; candidate proof replacement writes a separate full-file
copy. Context, wrappers and recursive termination clauses are preserved.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from survey import ROOT, STRATA_REV, mask_noncode, counts
import proof_tokens

REPO = ROOT / "sources/strata"
OUT = ROOT / "strata"
HELPER = ROOT / "scripts/ExtractDeclarations.lean"
URL = "https://github.com/strata-org/Strata"
_AUDITS: dict[tuple[str, str], dict] = {}


def sha(data: bytes | str) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def git(repo: Path, *args) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def lean_executable() -> str:
    explicit = os.environ.get("STRATA_LEAN_BIN")
    if explicit:
        return explicit
    return subprocess.check_output(["elan", "which", "lean"], text=True,
        env={**os.environ, "ELAN_TOOLCHAIN": "leanprover/lean4:v4.26.0"}).strip()


def run_parser(paths: list[Path], *, repo: Path | None = None, module: str | None = None) -> list[dict]:
    args = [lean_executable(), "--run", str(HELPER)]
    env = os.environ.copy()
    if repo is not None:
        env["LEAN_PATH"] = subprocess.check_output(["lake", "env", "printenv", "LEAN_PATH"], cwd=repo, text=True).strip()
        args.append("--source-imports")
    if module:
        args.append("--syntax-module=" + module)
    result = subprocess.run(args + [str(x.resolve()) for x in paths], cwd=repo or ROOT,
                            env=env, text=True, capture_output=True, timeout=600)
    if result.returncode:
        raise RuntimeError(f"Lean parser failed: {result.stderr}\n{result.stdout[:2000]}")
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def load_audits(path: Path = OUT / "parser_audit.jsonl"):
    if path.exists():
        for audit in read_jsonl(path):
            _AUDITS[(audit["file_path"], audit["file_sha256"])] = audit


def lexical_inventory(text: str) -> list[int]:
    """Independent declaration-keyword audit, not the boundary extractor."""
    masked = mask_noncode(text)
    pattern = r"(?m)^[ \t]*(?:(?:private|protected|public|noncomputable|unsafe)\s+)*(theorem|lemma)\b"
    return [m.start(1) for m in re.finditer(pattern, masked)]


def records_from_audit(text: str, file_path: str, audit: dict) -> dict:
    data = text.encode()
    masked = mask_noncode(text)
    records, excluded = [], []

    def char(byte):
        return len(data[:byte].decode())

    for node in audit.get("declarations", []):
        root, command, decl, value = (node[k] for k in
            ["root_command_range", "command_range", "declaration_range", "value_range"])
        if any(x is None for x in [root, command, decl, value]):
            raise ValueError(f"Missing native range: {file_path}: {node['name']}")
        root_text = data[root["start_byte"]:root["end_byte"]].decode()
        in_mutual = bool(re.match(r"\s*mutual\b", mask_noncode(root_text)))
        start = char(command["start_byte"] if in_mutual else root["start_byte"])
        end = char(value["end_byte"])
        # Drop leading doc comments, while keeping attrs and command wrappers.
        first_code = re.search(r"\S", masked[start:char(decl["start_byte"]) + 7])
        if first_code:
            start += first_code.start()
        assignment = node.get("assignment_range")
        delimiter_start = char(assignment["start_byte"] if assignment else value["start_byte"])
        proof_start = char(assignment["end_byte"] if assignment else value["start_byte"])
        src, proof = text[start:end], text[proof_start:end]
        statement = text[start:delimiter_start].rstrip()
        prefix = text[start:char(decl["start_byte"])]
        local_name = node["name"]
        namespace = node["namespace_syntactic"]
        name = local_name.removeprefix("_root_.") if local_name.startswith("_root_.") else ".".join([*namespace, local_name])
        incomplete = bool(re.search(r"\b(?:sorry|admit|sorryAx)\b", mask_noncode(proof)))
        style = "equations" if assignment is None else "by" if node["proof_kind"] == "Lean.Parser.Term.byTactic" else "term"
        start_line = text.count("\n", 0, start) + 1
        end_line = text.count("\n", 0, end - 1) + 1
        errors_in_span = [error for error in audit.get("errors", [])
                          if error.get("severity") == "error" and start_line <= error["line"] <= end_line]
        if errors_in_span:
            raise ValueError(f"Native parser errors inside {file_path}:{start_line}: {errors_in_span}")
        row = {
            "name": name, "source": "strata", "statement": statement, "src": src,
            "proof": proof, "proof_style": style, "declaration_kind": "theorem",
            "proof_length": proof_tokens.proof_length(src, statement) if assignment else None,
            "proof_length_method": "warmup_calibrated_appendix_J" if assignment else "not_defined_for_equation_form",
            "num_lines": len(src.splitlines()), "header": "", "file_path": file_path,
            "url": URL, "start_line": text.count("\n", 0, start) + 1,
            "end_line": text.count("\n", 0, end - 1) + 1,
            "declaration_line": text.count("\n", 0, char(decl["start_byte"])) + 1,
            "start_char": start, "end_char": end, "proof_start_char": proof_start,
            "start_byte": len(text[:start].encode()), "end_byte": value["end_byte"],
            "proof_start_byte": len(text[:proof_start].encode()),
            "value_start_byte": value["start_byte"], "value_end_byte": value["end_byte"],
            "proof_term_range": node.get("proof_range"),
            "version_info": [{"v4.26.0": STRATA_REV}],
            "namespace": namespace, "local_name": local_name,
            "name_resolution": "syntactic_namespace_qualified_not_kernel_resolved",
            "modifiers": re.findall(r"\b(private|protected|public|noncomputable|unsafe)\b", mask_noncode(prefix)),
            "wrappers": prefix, "mutual_context": root if in_mutual else None,
            "file_sha256": sha(data), "src_sha256": sha(src), "proof_sha256": sha(proof),
            "contains_sorry": incomplete,
            "native_parser_complete": not node["has_missing_syntax"],
            "parser_environment": audit.get("environment"),
            "heartbeat": None, "heartbeat_status": "not_measured",
            "compile_status": "not_checked_by_extractor", "axioms": None,
            "approximate_tactic_heads": counts(proof),
        }
        if node["has_missing_syntax"]:
            row["exclusion_reason"] = "incomplete_native_parse"
            excluded.append(row)
        elif incomplete:
            row["exclusion_reason"] = "explicit_sorry_or_admit_in_source_proof"
            excluded.append(row)
        elif style == "equations":
            row["exclusion_reason"] = "equation_style_requires_value_replacement_not_assignment_split"
            row["refactorable"] = True
            excluded.append(row)
        else:
            records.append(row)
    inventory = lexical_inventory(text)
    native_positions = [char(n["declaration_range"]["start_byte"]) for n in audit.get("declarations", [])]
    # A theorem node starts at the keyword (modifiers belong to its parent).
    if sorted(native_positions) != sorted(inventory):
        raise ValueError(f"Native/lexical declaration inventory differs for {file_path}: "
                         f"native={len(native_positions)}, lexical={len(inventory)}")
    return {"records": records, "excluded": excluded,
            "inventory": {"file_path": file_path, "declarations": len(inventory)}}


def extract_file(text: str, file_path: str) -> dict:
    if not _AUDITS:
        load_audits()
    audit = _AUDITS.get((file_path, sha(text)))
    if audit is None:
        cache = Path(os.environ.get("PROJECT_CACHE_DIR", "/Users/jwkweon/00_work/00_project/cache/05_pseudolab/LeanAgent-LeanRefactorArena")) / "extract-parser"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as folder:
            path = Path(folder) / "Input.lean"
            path.write_text(text)
            audit = run_parser([path])[0]
    return records_from_audit(text, file_path, audit)


def replace_proof(source: str, row: dict, new_proof: str) -> str:
    """Replace only proof text; equation rows accept `:= <new_proof>` values."""
    if sha(source) != row["file_sha256"] or source[row["start_char"]:row["end_char"]] != row["src"]:
        raise ValueError("Source hash/span mismatch; refusing to replace a different source revision")
    if not new_proof.strip():
        raise ValueError("Proof is empty")
    start = row["proof_start_char"]
    if row["proof_style"] == "equations":
        # Preserve equation branches verbatim or replace the entire value by
        # an assignment. In-place original-proof reinsertion is byte-identical.
        value = new_proof if new_proof.lstrip().startswith("|") else ":= " + new_proof
        return source[:start] + value + source[row["end_char"]:]
    return source[:start] + new_proof + source[row["end_char"]:]


def normalize_audit(audit: dict, repo: Path, files: dict[str, str]) -> dict:
    file_path = str(Path(audit["path"]).resolve().relative_to(repo.resolve()))
    result = dict(audit)
    result["file_path"] = file_path
    result["file_sha256"] = sha(files[file_path])
    result["path"] = file_path
    return result


def generate(args):
    repo, out = args.repo.resolve(), args.out.resolve()
    revision = git(repo, "rev-parse", "HEAD").decode().strip()
    if revision != STRATA_REV:
        raise ValueError(f"Expected pinned Strata {STRATA_REV}; got {revision}")
    tracked = [p.decode() for p in git(repo, "ls-tree", "-r", "--name-only", "-z", revision).split(b"\0") if p.endswith(b".lean")]
    files = {}
    for path in tracked:
        original = git(repo, "show", f"{revision}:{path}")
        if (repo / path).read_bytes() != original:
            raise ValueError(f"Modified upstream source: {path}")
        files[path] = original.decode()
    if args.audit_source:
        raw = read_jsonl(args.audit_source)
    elif (out / "parser_audit.jsonl").exists() and not args.reparse:
        raw = read_jsonl(out / "parser_audit.jsonl")
        for audit in raw:
            if sha(files[audit["file_path"]]) != audit["file_sha256"]:
                raise ValueError("Cached parser source hash mismatch")
        raw = [{**a, "path": str(repo / a["file_path"])} for a in raw]
    else:
        raw = run_parser([repo / p for p in tracked])
    audits = {a["file_path"]: a for a in (normalize_audit(a, repo, files) for a in raw)}
    for overlay in args.audit_overlay:
        for a in read_jsonl(overlay):
            a = normalize_audit(a, repo, files)
            audits[a["file_path"]] = a
    for path, audit in list(audits.items()):
        if any(n["has_missing_syntax"] for n in audit.get("declarations", [])):
            module = path.removesuffix(".lean").replace("/", ".")
            corrected = run_parser([repo / path], repo=repo, module=module)[0]
            audits[path] = normalize_audit(corrected, repo, files)
    if set(audits) != set(files):
        raise ValueError("Parser audit must cover every tracked Lean file")
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "parser_audit.jsonl", [audits[p] for p in tracked])
    all_rows, file_index = [], []
    for path, source in files.items():
        audit = audits[path]
        _AUDITS[(path, sha(source))] = audit
        extracted = records_from_audit(source, path, audit)
        rows = sorted(extracted["records"] + extracted["excluded"], key=lambda r: r["start_byte"])
        file_index.append({"file_path": path, "file_sha256": sha(source), "declarations": len(rows),
                           "native_file_parser_errors": len(audit.get("errors", [])),
                           "native_declarations_complete": all(r["native_parser_complete"] for r in rows)})
        if rows:
            context = out / "context" / path
            context.parent.mkdir(parents=True, exist_ok=True)
            context.write_text(source)
        all_rows.extend(rows)
    if len(all_rows) != 615 or any(not r["native_parser_complete"] for r in all_rows):
        raise ValueError(f"Expected615 complete syntax extractions; found{len(all_rows)}")
    rows_by_file = {}
    for index, row in enumerate(all_rows, 1):
        row["id"] = f"strata_{index:04d}"
        folder = out / "problems" / row["id"]
        folder.mkdir(parents=True, exist_ok=True)
        for filename, key in [("reference.lean", "src"), ("statement.lean", "statement"), ("proof.lean", "proof")]:
            (folder / filename).write_text(row[key])
        row["context_file"] = "context/" + row["file_path"]
        row["problem_dir"] = "problems/" + row["id"]
        row["source_link"] = f"{URL}/blob/{revision}/{row['file_path']}#L{row['start_line']}-L{row['end_line']}"
        write_json(folder / "metadata.json", {k:v for k,v in row.items() if k not in {"src", "statement", "proof"}})
        rows_by_file.setdefault(row["file_path"], []).append(row)
    direct = [r for r in all_rows if "exclusion_reason" not in r]
    equations = [r for r in all_rows if r["proof_style"] == "equations" and not r["contains_sorry"]]
    incomplete = [r for r in all_rows if r["contains_sorry"]]
    write_jsonl(out / "benchmark.jsonl", direct)
    write_jsonl(out / "equations.jsonl", equations)
    write_jsonl(out / "excluded.jsonl", incomplete)
    write_jsonl(out / "inventory.jsonl", all_rows)
    write_json(out / "files.json", file_index)
    for name in ["LICENSE-MIT", "LICENSE-APACHE", "NOTICE"]:
        (out / name).write_bytes(git(repo, "show", f"{revision}:{name}"))
    (out / "environment").mkdir(exist_ok=True)
    for name in ["lean-toolchain", "lake-manifest.json", "lakefile.toml"]:
        (out / "environment" / name).write_bytes(git(repo, "show", f"{revision}:{name}"))
    snapshot = ROOT / "data/arena_snapshot.json"
    if snapshot.exists():
        arena_revision = json.loads(snapshot.read_text())["arena_revision"]
        warmups = read_jsonl(ROOT / "data/arena" / arena_revision / "benchmark_data_warmup.jsonl")
        by_name = {r["name"]: r for r in all_rows}
        checks = []
        for number, warmup in enumerate(warmups, 1):
            if warmup["source"] != "strata":
                continue
            row = by_name[warmup["name"]]
            check = {"warmup_number": number, "id": row["id"], "name": row["name"],
                     "equal_fields": {k: row[k] == warmup[k] for k in ["src", "statement", "proof_length", "num_lines", "header"]}}
            if not all(check["equal_fields"].values()):
                raise ValueError(f"Warmup mismatch: {check}")
            checks.append(check)
        write_json(out / "warmup_matches.json", {"arena_revision": arena_revision, "checks": checks})
    summary = {"source": URL, "revision": revision, "toolchain": "leanprover/lean4:v4.26.0",
               "files_scanned": len(files), "files_with_declarations": len(rows_by_file),
               "total_declarations": len(all_rows), "warmup_shaped_complete_source": len(direct),
               "equation_style_complete_source": len(equations), "direct_incomplete_source": len(incomplete),
               "declaration_kinds": dict(Counter(r["declaration_kind"] for r in all_rows)),
               "proof_styles": dict(Counter(r["proof_style"] for r in all_rows)),
               "private_declarations": sum("private" in r["modifiers"] for r in all_rows),
               "mutual_declarations": sum(r["mutual_context"] is not None for r in all_rows),
               "extractor_sha256": sha(Path(__file__).read_bytes()), "lean_parser_sha256": sha(HELPER.read_bytes()),
               "proof_tokens_sha256": sha((ROOT / "scripts/proof_tokens.py").read_bytes()),
               "validation_scope": "native syntax and exact source spans; no elaboration or heartbeat by extractor"}
    write_json(out / "manifest.json", summary)
    render_index(out, summary, rows_by_file)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def export_verified(out: Path):
    """Keep raw extraction immutable; publish an axiom-checked derived subset."""
    rows = read_jsonl(out / "inventory.jsonl")
    summary = json.loads((out / "validation/summary.json").read_text())
    if summary["inventory_sha256"] != sha((out / "inventory.jsonl").read_bytes()):
        raise ValueError("Validation evidence belongs to a different inventory; rerun validation")
    evidence = {r["id"]: r for r in read_jsonl(out / "validation/declarations.jsonl")}
    verified, equations, rejected = [], [], []
    permitted = {"propext", "Classical.choice", "Quot.sound"}
    for row in rows:
        result = evidence[row["id"]]
        if result["source_sha256"] != row["file_sha256"] or result["start_byte"] != row["start_byte"] or result["end_byte"] != row["end_byte"]:
            raise ValueError(f"Validation source span mismatch: {row['id']}")
        enriched = {**row, "validation": result,
                    "compile_status": "original_module_build_passed" if result["module_build_passed"] else "failed",
                    "axioms": result.get("axioms"), "kernel_name": result.get("kernel_name")}
        clean = (result.get("module_build_passed") is True
                 and result.get("kernel_mapping_status") == "unique"
                 and result.get("original_proof_axioms_checked") is True
                 and row.get("native_parser_complete") is True
                 and not row.get("contains_sorry", True)
                 and result.get("has_sorryAx") is False
                 and isinstance(result.get("axioms"), list)
                 and set(result["axioms"]) <= permitted)
        if clean:
            (equations if row["proof_style"] == "equations" else verified).append(enriched)
        else:
            rejected.append(enriched)
        metadata = {k:v for k,v in enriched.items() if k not in {"src", "statement", "proof"}}
        write_json(out / row["problem_dir"] / "metadata.json", metadata)
    write_jsonl(out / "verified_benchmark.jsonl", verified)
    write_jsonl(out / "verified_equations.jsonl", equations)
    write_jsonl(out / "axiom_excluded.jsonl", rejected)
    report = {"input_inventory_sha256": sha((out / "inventory.jsonl").read_bytes()),
              "validation_sha256": sha((out / "validation/declarations.jsonl").read_bytes()),
              "verified_assignment_proofs": len(verified), "verified_equation_proofs": len(equations),
              "excluded_by_axioms": len(rejected), "permitted_axioms": sorted(permitted),
              "scope": "Original compiled proofs only; candidate rewrites require fresh validation. No heartbeat measured."}
    write_json(out / "verified_manifest.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def render_index(out: Path, summary: dict, by_file: dict):
    lines = ["# Strata 정리 추출 목록", "", "고정 커밋의 모든 Lean 파일에서 정리 선언과 증명 본문을 추출한 목록입니다.", "",
             f"{summary['files_scanned']}파일 → {summary['files_with_declarations']}파일의 {summary['total_declarations']}개 정리.", "",
             "`benchmark.jsonl`은 `:=` 형태이며 원문에 직접 sorry가 없는 선언입니다. 증명의 전이적 공리 검증과는 구분합니다.", "",
             "| 파일 | 전체 정리 | 직접 미완성 | 식 패턴 증명 |", "| --- | ---: | ---: | ---: |"]
    for path, rows in by_file.items():
        index_path = Path("modules") / Path(path).with_suffix(".md")
        lines.append(f"| [{path}]({index_path.as_posix()}) | {len(rows)} | {sum(r['contains_sorry'] for r in rows)} | {sum(r['proof_style']=='equations' for r in rows)} |")
        target = out / index_path
        target.parent.mkdir(parents=True, exist_ok=True)
        module = [f"# {path}", "", f"추출한 정리 {len(rows)}개. 원본 전체 문맥을 유지한 상태에서 증명 본문을 교체해야 합니다.", "",
                  "| ID | 정리 | 원본 줄 | 증명 형태 | 직접 sorry |", "| --- | --- | ---: | --- | --- |"]
        for row in rows:
            ref = os.path.relpath(out / row["problem_dir"] / "reference.lean", target.parent)
            module.append(f"| {row['id']} | [{row['name']}]({ref}) | {row['start_line']}–{row['end_line']} | {row['proof_style']} | {'있음' if row['contains_sorry'] else '없음'} |")
        target.write_text("\n".join(module) + "\n")
    (out / "index.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract")
    extract.add_argument("--repo", type=Path, default=REPO)
    extract.add_argument("--out", type=Path, default=OUT)
    extract.add_argument("--audit-source", type=Path)
    extract.add_argument("--audit-overlay", type=Path, action="append", default=[])
    extract.add_argument("--reparse", action="store_true")
    replace = sub.add_parser("replace")
    replace.add_argument("--id", required=True)
    replace.add_argument("--proof", type=Path, required=True)
    replace.add_argument("--output", type=Path, required=True)
    replace.add_argument("--dataset", type=Path, default=OUT)
    verified = sub.add_parser("export-verified")
    verified.add_argument("--dataset", type=Path, default=OUT)
    args = parser.parse_args()
    if args.command == "extract":
        generate(args)
    elif args.command == "export-verified":
        export_verified(args.dataset)
    else:
        row = next(r for r in read_jsonl(args.dataset / "inventory.jsonl") if r["id"] == args.id)
        source_path = args.dataset / row["context_file"]
        if (args.output.resolve().is_relative_to(args.dataset.resolve())
                or args.output.resolve().is_relative_to(REPO.resolve())
                or args.output.resolve() == args.proof.resolve()):
            raise ValueError("Write the candidate outside the dataset and pinned source, without overwriting the input proof")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(replace_proof(source_path.read_text(), row, args.proof.read_text()))
        print(f"Wrote full-context candidate {args.output}; compilation still required")


if __name__ == "__main__":
    main()
