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
import sys
import tempfile

from survey import ROOT, mask_noncode, counts
PHYSLIB_REV = "c48433678e8fb6306ebcd48453300c8e16058a62"
import proof_tokens
from physlib_lexical import declaration_positions as lexical_inventory

REPO = ROOT / "sources/physlib"
OUT = ROOT / "physlib"
HELPER = ROOT / "scripts/ExtractPhyslibDeclarations.lean"
URL = "https://github.com/leanprover-community/physlib"
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
    explicit = os.environ.get("PHYSLIB_LEAN_BIN")
    if explicit:
        return explicit
    return subprocess.check_output(["elan", "which", "lean"], text=True,
        env={**os.environ, "ELAN_TOOLCHAIN": "leanprover/lean4:v4.32.0"}).strip()


def run_parser(paths: list[Path], *, repo: Path | None = None, module: str | None = None) -> list[dict]:
    args = [lean_executable(), "--run", str(HELPER)]
    env = os.environ.copy()
    env["LEAN_PATH"] = subprocess.check_output(["lake", "env", "printenv", "LEAN_PATH"], cwd=repo or REPO, text=True).strip()
    if repo is not None:
        args.append("--source-imports")
    args.append("--syntax-module=" + (module or "Mathlib.Tactic.Lemma"))
    result = subprocess.run(args + [str(x.resolve()) for x in paths], cwd=repo or REPO,
                            env=env, text=True, capture_output=True, timeout=600)
    if result.returncode:
        raise RuntimeError(f"Lean parser failed: {result.stderr}\n{result.stdout[:2000]}")
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def load_audits(path: Path = OUT / "parser_audit.jsonl"):
    if path.exists():
        for audit in read_jsonl(path):
            _AUDITS[(audit["file_path"], audit["file_sha256"])] = audit


def records_from_audit(text: str, file_path: str, audit: dict) -> dict:
    data = text.encode()
    masked = mask_noncode(text)
    records, excluded, unresolved = [], [], []

    def char(byte):
        return len(data[:byte].decode())

    for node in audit.get("declarations", []):
        root, command, decl, value = (node[k] for k in
            ["root_command_range", "command_range", "declaration_range", "value_range"])
        if any(x is None for x in [root, command, decl, value]) or (node["has_missing_syntax"] and not node.get("layout_recovered")):
            unresolved.append({"file_path": file_path, "local_name": node.get("name"),
                               "declaration_range": decl, "reason": "incomplete_native_parse",
                               "native_node": node, "parser_errors": audit.get("errors", [])})
            continue
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
        style = ("structure" if node["value_kind"] == "Lean.Parser.Command.whereStructInst" else "equations") if assignment is None else "by" if node["proof_kind"] == "Lean.Parser.Term.byTactic" else "term"
        start_line = text.count("\n", 0, start) + 1
        end_line = text.count("\n", 0, end - 1) + 1
        errors_in_span = [error for error in audit.get("errors", [])
                          if error.get("severity") == "error" and start_line <= error["line"] <= end_line]
        if errors_in_span and not node.get("layout_recovered"):
            unresolved.append({"file_path": file_path, "local_name": node.get("name"),
                               "declaration_range": decl, "reason": "native_error_in_declaration",
                               "native_node": node, "parser_errors": errors_in_span})
            continue
        row = {
            "name": name, "source": "physlib", "statement": statement, "src": src,
            "proof": proof, "proof_style": style, "declaration_kind": node.get("declaration_kind", text[char(decl["start_byte"]):].split()[0]),
            "proof_length": proof_tokens.proof_length(src, statement) if assignment else None,
            "proof_length_method": "warmup_calibrated_appendix_J" if assignment else "not_defined_for_equation_form",
            "num_lines": len(src.splitlines()), "header": "", "file_path": file_path,
            "url": URL, "start_line": text.count("\n", 0, start) + 1,
            "end_line": text.count("\n", 0, end - 1) + 1,
            "declaration_line": text.count("\n", 0, char(decl["start_byte"])) + 1,
            "declaration_start_byte": decl["start_byte"],
            "start_char": start, "end_char": end, "proof_start_char": proof_start,
            "start_byte": len(text[:start].encode()), "end_byte": value["end_byte"],
            "proof_start_byte": len(text[:proof_start].encode()),
            "value_start_byte": value["start_byte"], "value_end_byte": value["end_byte"],
            "proof_term_range": node.get("proof_range"),
            "proof_with_suffix_range": node.get("proof_with_suffix_range"),
            "termination_suffix_range": node.get("termination_suffix_range"),
            "where_declarations_range": node.get("where_declarations_range"),
            "version_info": [{"v4.32.0": PHYSLIB_REV}],
            "namespace": namespace, "local_name": local_name,
            "name_resolution": "syntactic_namespace_qualified_not_kernel_resolved",
            "modifiers": re.findall(r"\b(private|protected|public|noncomputable|unsafe|nonrec)\b", mask_noncode(prefix)),
            "wrappers": prefix, "mutual_context": root if in_mutual else None,
            "file_sha256": sha(data), "src_sha256": sha(src), "proof_sha256": sha(proof),
            "contains_sorry": incomplete,
            "native_parser_complete": not node["has_missing_syntax"],
            "extraction_method": "layout_with_native_start_anchor" if node.get("layout_recovered") else "native_lean_ast",
            "parser_environment": audit.get("environment"),
            "heartbeat": None, "heartbeat_status": "not_measured",
            "compile_status": "not_checked_by_extractor", "axioms": None,
            "approximate_tactic_heads": counts(proof),
        }
        if node["has_missing_syntax"] and not node.get("layout_recovered"):
            row["exclusion_reason"] = "incomplete_native_parse"
            excluded.append(row)
        elif incomplete:
            row["exclusion_reason"] = "explicit_sorry_or_admit_in_source_proof"
            excluded.append(row)
        elif style in {"equations", "structure"}:
            row["exclusion_reason"] = "non_assignment_value_requires_special_replacement"
            row["refactorable"] = True
            excluded.append(row)
        else:
            records.append(row)
    inventory = lexical_inventory(text)
    native_positions = [char(n["declaration_range"]["start_byte"]) for n in audit.get("declarations", []) if n.get("declaration_range")]
    # A theorem node starts at the keyword (modifiers belong to its parent).
    unexpected = set(native_positions) - set(inventory)
    if unexpected or len(native_positions) != len(set(native_positions)):
        raise ValueError(f"Unexpected/duplicate native declarations for {file_path}: {unexpected}")
    for position in sorted(set(inventory) - set(native_positions)):
        unresolved.append({"file_path": file_path, "reason": "lexical_declaration_missing_from_native_parse",
                           "keyword_char": position, "keyword_byte": len(text[:position].encode()),
                           "line": text.count("\n", 0, position) + 1,
                           "parser_errors": audit.get("errors", [])})
    for item in unresolved:
        start_byte = item.get("keyword_byte", (item.get("declaration_range") or {}).get("start_byte"))
        item["declaration_start_byte"] = start_byte
        item["declaration_line"] = text.count("\n", 0, char(start_byte)) + 1 if start_byte is not None else None
    return {"records": records, "excluded": excluded, "unresolved": unresolved,
            "inventory": {"file_path": file_path, "declarations": len(inventory)}}


def extract_file(text: str, file_path: str) -> dict:
    if not _AUDITS:
        load_audits()
    audit = _AUDITS.get((file_path, sha(text)))
    if audit is None:
        cache = Path(os.environ.get("PROJECT_CACHE_DIR", "/Users/jwkweon/00_work/00_project/cache/05_pseudolab/LeanAgent-LeanRefactorArena")) / "physlib-extract-parser"
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
    if row["proof_style"] in {"equations", "structure"}:
        # Preserve equation branches verbatim or replace the entire value by
        # an assignment. In-place original-proof reinsertion is byte-identical.
        value = new_proof if new_proof.lstrip().startswith(("|", "where")) else ":= " + new_proof
        return source[:start] + value + source[row["end_char"]:]
    return source[:start] + new_proof + source[row["end_char"]:]


def normalize_audit(audit: dict, repo: Path, files: dict[str, str]) -> dict:
    audit_path = Path(audit["path"])
    file_path = str((audit_path if audit_path.is_absolute() else repo / audit_path).resolve().relative_to(repo.resolve()))
    result = dict(audit)
    result["file_path"] = file_path
    result["file_sha256"] = sha(files[file_path])
    result["path"] = file_path
    return result


def generate(args):
    repo, out = args.repo.resolve(), args.out.resolve()
    revision = git(repo, "rev-parse", "HEAD").decode().strip()
    if revision != PHYSLIB_REV:
        raise ValueError(f"Expected pinned Physlib {PHYSLIB_REV}; got {revision}")
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
        parser_output = out / "parser_audit.jsonl"
        subprocess.run([sys.executable, str(ROOT / "scripts/parse_physlib.py"),
                        "--repo", str(repo), "--output", str(parser_output)], check=True)
        raw = read_jsonl(parser_output)
        raw = [{**a, "path": str(repo / a.get("file_path", a["path"]))} for a in raw]
    audits = {a["file_path"]: a for a in (normalize_audit(a, repo, files) for a in raw)}
    for overlay in args.audit_overlay:
        for a in read_jsonl(overlay):
            a = normalize_audit(a, repo, files)
            audits[a["file_path"]] = a
    if set(audits) != set(files):
        raise ValueError("Parser audit must cover every tracked Lean file")
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "parser_audit.jsonl", [audits[p] for p in tracked])
    all_rows, file_index, unresolved = [], [], []
    calibration = {"compared": 0, "matched": 0, "recovered": 0, "failures": []}
    previous_ids = {(r["file_path"], r["declaration_start_byte"]): r["id"]
                    for r in read_jsonl(out / "inventory.jsonl")} if (out / "inventory.jsonl").exists() else {}
    for path, source in files.items():
        audit = audits[path]
        _AUDITS[(path, sha(source))] = audit
        extracted = records_from_audit(source, path, audit)
        if args.layout_recovery:
            from physlib_layout import Layout, recovered_node
            layout = Layout(source)
            complete = {r["declaration_start_byte"]: r for r in extracted["records"] + extracted["excluded"]}
            new_nodes = []
            for node in audit["declarations"]:
                position = node["declaration_range"]["start_byte"]
                try:
                    span = layout.extract(node)
                    if position in complete:
                        calibration["compared"] += 1
                        if any(span[k] != complete[position][k] for k in ["src", "statement", "proof"]):
                            raise ValueError("Layout/native boundary calibration mismatch")
                        calibration["matched"] += 1
                    else:
                        node = recovered_node(source, node, span)
                        calibration["recovered"] += 1
                except ValueError as error:
                    if position in complete:
                        raise ValueError(f"Calibration failed {path}:{node['name']}: {error}")
                    calibration["failures"].append({"file_path": path, "name": node["name"], "reason": str(error)})
                new_nodes.append(node)
            extracted = records_from_audit(source, path, {**audit, "declarations": new_nodes})
        rows = sorted(extracted["records"] + extracted["excluded"], key=lambda r: r["start_byte"])
        for item in extracted["unresolved"]:
            item.update(file_sha256=sha(source), context_file="context/" + path,
                        source_link=f"{URL}/blob/{revision}/{path}")
            unresolved.append(item)
        file_index.append({"file_path": path, "file_sha256": sha(source), "declarations": len(rows),
                           "lexical_declarations": extracted["inventory"]["declarations"],
                           "unresolved_declarations": len(extracted["unresolved"]),
                           "native_file_parser_errors": len(audit.get("errors", [])),
                           "native_declarations_complete": all(r["native_parser_complete"] for r in rows)})
        if rows or extracted["unresolved"]:
            context = out / "context" / path
            context.parent.mkdir(parents=True, exist_ok=True)
            context.write_text(source)
        all_rows.extend(rows)
    if not all_rows or any(not r["native_parser_complete"] and r["extraction_method"] != "layout_with_native_start_anchor" for r in all_rows):
        raise ValueError(f"Incomplete native syntax extraction: {len(all_rows)} declarations")
    if len(all_rows) + len(unresolved) != sum(f["lexical_declarations"] for f in file_index):
        raise ValueError("Complete and unresolved declarations do not partition the lexical inventory")
    rows_by_file = {}
    next_id = max((int(v.split('_')[1]) for v in previous_ids.values()), default=0) + 1
    for row in all_rows:
        row["id"] = previous_ids.get((row["file_path"], row["declaration_start_byte"]))
        if row["id"] is None:
            row["id"] = f"physlib_{next_id:04d}"
            next_id += 1
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
    structures = [r for r in all_rows if r["proof_style"] == "structure" and not r["contains_sorry"]]
    incomplete = [r for r in all_rows if r["contains_sorry"]]
    write_jsonl(out / "benchmark.jsonl", direct)
    write_jsonl(out / "equations.jsonl", equations)
    write_jsonl(out / "structures.jsonl", structures)
    write_jsonl(out / "excluded.jsonl", incomplete)
    write_jsonl(out / "inventory.jsonl", all_rows)
    write_jsonl(out / "unresolved_declarations.jsonl", unresolved)
    write_json(out / "files.json", file_index)
    if args.layout_recovery:
        write_json(out / "layout_validation.json", calibration)
    for name in ["LICENSE"]:
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
            if warmup["source"] != "physlib":
                continue
            if warmup["name"] not in by_name:
                checks.append({"warmup_number": number, "name": warmup["name"],
                               "status": "not_yet_extracted", "equal_fields": {}})
                continue
            row = by_name[warmup["name"]]
            check = {"warmup_number": number, "id": row["id"], "name": row["name"],
                     "equal_fields": {k: row[k] == warmup[k] for k in ["src", "statement", "proof_length", "num_lines", "header"]}}
            if not all(check["equal_fields"].values()):
                raise ValueError(f"Warmup mismatch: {check}")
            checks.append(check)
        write_json(out / "warmup_matches.json", {"arena_revision": arena_revision, "checks": checks})
    summary = {"source": URL, "revision": revision, "toolchain": "leanprover/lean4:v4.32.0",
               "files_scanned": len(files), "files_with_declarations": len(rows_by_file),
               "total_declarations": len(all_rows), "warmup_shaped_complete_source": len(direct),
               "lexical_declarations": sum(f["lexical_declarations"] for f in file_index),
               "unresolved_declarations": len(unresolved),
               "equation_style_complete_source": len(equations), "direct_incomplete_source": len(incomplete),
               "structure_style_complete_source": len(structures),
               "declaration_kinds": dict(Counter(r["declaration_kind"] for r in all_rows)),
               "proof_styles": dict(Counter(r["proof_style"] for r in all_rows)),
               "private_declarations": sum("private" in r["modifiers"] for r in all_rows),
               "mutual_declarations": sum(r["mutual_context"] is not None for r in all_rows),
               "extractor_sha256": sha(Path(__file__).read_bytes()), "lean_parser_sha256": sha(HELPER.read_bytes()),
               "lexical_audit_sha256": sha((ROOT / "scripts/physlib_lexical.py").read_bytes()),
               "extraction_methods": dict(Counter(r["extraction_method"] for r in all_rows)),
               "layout_recovery": args.layout_recovery,
               "layout_parser_sha256": sha((ROOT / "scripts/physlib_layout.py").read_bytes()) if args.layout_recovery else None,
               "proof_tokens_sha256": sha((ROOT / "scripts/proof_tokens.py").read_bytes()),
               "validation_scope": "Native AST spans plus explicitly labeled, native-calibrated source-layout recovery when enabled; no elaboration or heartbeat by extractor"}
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
    verified, equations, structures, rejected, unverified = [], [], [], [], []
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
            (equations if row["proof_style"] == "equations" else structures if row["proof_style"] == "structure" else verified).append(enriched)
        elif not row.get("native_parser_complete"):
            enriched["verification_exclusion_reason"] = "layout_extraction_requires_additional_native_or_candidate_validation"
            unverified.append(enriched)
        elif not (result.get("module_build_passed") is True
                  and result.get("kernel_mapping_status") == "unique"
                  and result.get("original_proof_axioms_checked") is True):
            enriched["verification_exclusion_reason"] = result.get("failure_reason", "original_proof_not_verified")
            unverified.append(enriched)
        else:
            enriched["verification_exclusion_reason"] = "disallowed_transitive_axioms"
            rejected.append(enriched)
        metadata = {k:v for k,v in enriched.items() if k not in {"src", "statement", "proof"}}
        write_json(out / row["problem_dir"] / "metadata.json", metadata)
    write_jsonl(out / "verified_benchmark.jsonl", verified)
    write_jsonl(out / "verified_equations.jsonl", equations)
    write_jsonl(out / "verified_structures.jsonl", structures)
    write_jsonl(out / "axiom_excluded.jsonl", rejected)
    write_jsonl(out / "unverified.jsonl", unverified)
    report = {"input_inventory_sha256": sha((out / "inventory.jsonl").read_bytes()),
              "validation_sha256": sha((out / "validation/declarations.jsonl").read_bytes()),
              "verified_assignment_proofs": len(verified), "verified_equation_proofs": len(equations),
              "verified_structure_proofs": len(structures),
              "excluded_by_axioms": len(rejected), "unverified": len(unverified),
              "permitted_axioms": sorted(permitted),
              "scope": "Original compiled proofs only; candidate rewrites require fresh validation. No heartbeat measured."}
    write_json(out / "verified_manifest.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def render_index(out: Path, summary: dict, by_file: dict):
    lines = ["# Physlib 정리 추출 목록", "", "고정 커밋의 모든 Lean 파일에서 정리 선언과 증명 본문을 추출한 목록입니다.", "",
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
    extract.add_argument("--layout-recovery", action="store_true", help="Add explicitly labeled layout-based spans after exact native calibration")
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
