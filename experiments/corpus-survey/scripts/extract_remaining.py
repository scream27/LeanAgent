#!/usr/bin/env python3
"""Bounded, Python-only lexical/layout extraction; never executes upstream Lean.

Declaration identities, namespaces and ranges are syntactic hypotheses, not AST
or kernel facts. Unrecognized declaration anchors and boundary failures are kept
in an unresolved ledger with the original full-file context.
"""
from __future__ import annotations

import argparse
from array import array
import bisect
from collections import Counter
from contextlib import ExitStack
import hashlib
import gzip
import json
from pathlib import Path
import re
import subprocess
import shutil

from physlib_layout import Layout, COMMAND, code_mask
from survey import counts
import proof_tokens

from arena_workspace import ROOT
MODIFIERS = r"private|protected|public|noncomputable|unsafe|nonrec|meta|partial"
IDENT = r"(?:«[^»]+»|[^\W\d][\w'₀-₉]*)(?:\.(?:«[^»]+»|[^\W\d][\w'₀-₉]*))*"
KEYWORDS = re.compile(r"(?<![\w.`])\b(theorem|lemma)\b")
WRAPPER = re.compile(r"^(?:set_option|open|include|omit|attribute)\b[\s\S]*\bin\s*$")
RAW_STRING = re.compile(r'r(#+)"')
CHAR_LITERAL = re.compile(r"'(?:\\.|[^'\n])'")


def mask_noncode(source):
    """Offset-preserving scanner equivalent to survey.mask_noncode, linear-time."""
    out, i, n = list(source), 0, len(source)
    while i < n:
        start = i
        if source.startswith('--', i):
            end = source.find('\n', i)
            i = n if end < 0 else end
        elif source.startswith('/-', i):
            depth, i = 1, i + 2
            while i < n and depth:
                if source.startswith('/-', i): depth, i = depth + 1, i + 2
                elif source.startswith('-/', i): depth, i = depth - 1, i + 2
                else: i += 1
        elif (raw := RAW_STRING.match(source, i)) and (i == 0 or not source[i-1].isalnum()):
            close = '"' + raw[1]
            end = source.find(close, raw.end())
            i = n if end < 0 else end + len(close)
        elif source[i] == '"':
            i += 1
            while i < n:
                if source[i] == '\\': i = min(n, i + 2)
                elif source[i] == '"': i += 1; break
                else: i += 1
        elif source[i] == "'" and (i == 0 or not re.match(r"[\w']", source[i-1])) and (char := CHAR_LITERAL.match(source, i)):
            i = char.end()
        else:
            i += 1
            continue
        for pos in range(start, i):
            if out[pos] != '\n': out[pos] = ' '
    return ''.join(out)


def mask_syntax_quotations(source):
    chars = list(mask_noncode(source))
    i = 0
    while i < len(chars) - 1:
        if chars[i] != '`' or chars[i+1] != '(':
            i += 1
            continue
        end, depth = i + 2, 1
        while end < len(chars) and depth:
            depth += (chars[end] == '(') - (chars[end] == ')')
            end += 1
        for pos in range(i, end):
            if chars[pos] not in '\r\n': chars[pos] = ' '
        i = end
    return ''.join(chars)


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def strip_prefix(prefix):
    """Consume only recognized attributes, modifiers, and command wrappers."""
    rest = prefix.strip()
    while rest:
        if rest.startswith("@["):
            depth, end = 1, 2
            while end < len(rest) and depth:
                depth += (rest[end] == "[") - (rest[end] == "]")
                end += 1
            if depth:
                return False
            rest = rest[end:].lstrip()
        elif match := re.match(r"(?:" + MODIFIERS + r")\b\s*", rest):
            rest = rest[match.end():]
        elif re.match(r"(?:set_option|open|include|omit|attribute)\b", rest):
            # An inline wrapper must terminate at `in`, before the declaration.
            matches = list(re.finditer(r"\bin\b", rest))
            if not matches:
                return False
            rest = rest[matches[-1].end():].lstrip()
        else:
            return False
    return True


def root_start(masked, keyword):
    """Start at attributes/wrappers attached to a declaration, excluding docs."""
    begin = masked.rfind("\n", 0, keyword) + 1
    prefix = masked[begin:keyword]
    if not strip_prefix(prefix):
        return None
    root = begin
    # Backtrack over complete, adjacent attributes/modifiers/wrappers. Balancing
    # permits an attribute split over several lines without absorbing old commands.
    cursor = begin
    while cursor:
        previous_end = cursor - 1
        previous_begin = masked.rfind("\n", 0, previous_end) + 1
        previous = masked[previous_begin:previous_end].strip()
        if not previous:
            cursor = previous_begin
            continue
        if previous.endswith("]") and not previous.startswith("@["):
            attr_begin = masked.rfind("@[", 0, previous_end)
            if attr_begin >= 0 and strip_prefix(masked[attr_begin:previous_end]):
                previous_begin = masked.rfind("\n", 0, attr_begin) + 1
                previous = masked[previous_begin:previous_end].strip()
        if strip_prefix(previous):
            root = previous_begin
            cursor = previous_begin
        else:
            break
    first = re.search(r"\S", masked[root:keyword + 7])
    return root + first.start() if first else keyword


def namespace_events(masked):
    events = []
    for m in re.finditer(r"(?m)^[ \t]*(?:(?:noncomputable|public|private)\s+)*(namespace|section|end|mutual)\b[^\n]*", masked):
        name = re.match(r"\s*(" + IDENT + r")", masked[m.start(1) + len(m[1]):m.end()])
        events.append((m.start(), m[1], name[1] if name else ""))
    return events


def extract_text(text, file_path, source, revision, toolchain="", url=""):
    masked = mask_syntax_quotations(text)
    # Identifiers in guillemets can contain reserved words; keep their offsets
    # opaque for command/anchor discovery, while reading real names from source.
    masked = re.sub(r"«[^»]*»", lambda m: "x" * len(m[0]), masked)
    layout = Layout.__new__(Layout)
    layout.text, layout.code = text, code_mask(text)
    layout.command_code = mask_syntax_quotations(layout.code)
    layout.commands = [(m.start(), len(m[1] if m[1] is not None else m[2])) for m in COMMAND.finditer(layout.command_code)]
    layout.starts = [x[0] for x in layout.commands]
    # A do-notation bind uses ←, not :=; it must not consume the declaration's
    # later := as if it were the binding value. Preserve all offsets.
    code_chars = list(layout.code)
    for binding in re.finditer(r"\blet\b", layout.code):
        delimiter = re.search(r"←|:=|\bin\b|;", layout.code[binding.end():])
        if delimiter and delimiter[0] == "←":
            code_chars[binding.start():binding.end()] = " " * len(binding[0])
    layout.code = "".join(code_chars)
    events = namespace_events(masked)
    event_index, frames = 0, []
    records, unresolved = [], []
    byte_offsets, byte_count = array('I', [0]), 0
    for character in text:
        byte_count += 1 if ord(character) < 128 else len(character.encode())
        byte_offsets.append(byte_count)
    byte = lambda pos: byte_offsets[pos]
    file_hash = sha(text)
    candidates = list(KEYWORDS.finditer(masked))
    for match in candidates:
        keyword = match.start()
        while event_index < len(events) and events[event_index][0] < keyword:
            _, kind, name = events[event_index]
            event_index += 1
            if kind == "end":
                if frames:
                    frames.pop()
            else:
                frames.append((kind, name))
        root = root_start(masked, keyword)
        issue = {"file_path": file_path, "declaration_start_byte": byte(keyword),
                 "declaration_line": text.count("\n", 0, keyword) + 1,
                 "file_sha256": file_hash, "context_file": "context/" + file_path,
                 "extraction_method": "lexical_layout", "native_parser_complete": False}
        if root is None:
            issue["reason"] = "unrecognized_declaration_prefix_or_keyword_reference"
            unresolved.append(issue)
            continue
        name_start = match.end()
        while name_start < len(masked) and masked[name_start].isspace():
            name_start += 1
        name_match = re.match(IDENT, text[name_start:])
        if not name_match:
            unresolved.append(dict(issue, reason="missing_or_unrecognized_declaration_name"))
            continue
        local_name = name_match[0]
        namespace = [name for kind, name in frames if kind == "namespace"]
        name = local_name.removeprefix("_root_.") if local_name.startswith("_root_.") else ".".join([*namespace, local_name])
        node = {"declaration_range": {"start_byte": byte(keyword)},
                "root_command_range": {"start_byte": byte(root)}}
        try:
            span = layout.extract(node)
            # A boundary must not swallow another lexical theorem declaration.
            if any(keyword < other.start() < span["end_char"] for other in candidates):
                raise ValueError("overlapping_declaration_anchors")
            if not span["proof"].strip():
                raise ValueError("empty_source_proof")
        except ValueError as error:
            unresolved.append(dict(issue, name=name, reason=str(error)))
            continue
        start, end, proof_start = (span[k] for k in ["start_char", "end_char", "proof_start_char"])
        root_command_start = start
        # Arena records the declaration, while outer scoped-command wrappers
        # remain in context. Keep attributes/modifiers after the final `in`.
        prefix_mask = masked[start:keyword]
        if re.match(r"(?:set_option|open|include|omit|attribute)\b", prefix_mask):
            wrappers = list(re.finditer(r"\bin\b", prefix_mask))
            if wrappers:
                after_wrapper = start + wrappers[-1].end()
                first = re.search(r"\S", masked[after_wrapper:keyword + 7])
                start = after_wrapper + first.start()
                span.update(start_char=start, src=text[start:end], statement=text[start:span['delimiter_start_char']].rstrip())
        assignment = span["value_style"] == "assignment"
        style = "by" if assignment and re.match(r"\s*by\b", code_mask(span["proof"])) else "term" if assignment else span["value_style"]
        incomplete = bool(re.search(r"\b(?:sorry|admit|sorryAx)\b", mask_syntax_quotations(span["proof"])))
        prefix = text[start:keyword]
        row = {**span, "name": name, "source": source, "proof_style": style,
               "declaration_kind": match[1], "local_name": local_name, "namespace": namespace,
               "name_resolution": "syntactic_namespace_qualified_not_kernel_resolved",
               "file_path": file_path, "url": url, "header": "",
               "start_line": text.count("\n", 0, start) + 1,
               "end_line": text.count("\n", 0, max(start, end - 1)) + 1,
               "declaration_line": issue["declaration_line"],
               "declaration_start_byte": byte(keyword), "start_byte": byte(start), "end_byte": byte(end),
               "proof_start_byte": byte(proof_start), "value_start_byte": byte(span["delimiter_start_char"]), "value_end_byte": byte(end),
               "proof_length": proof_tokens.proof_length(span["src"], span["statement"]) if assignment else None,
               "proof_length_method": "warmup_calibrated_appendix_J" if assignment else "not_defined_for_non_assignment",
               "num_lines": len(span["src"].splitlines()),
               "modifiers": re.findall(r"\b(" + MODIFIERS + r")\b", mask_noncode(prefix)), "wrappers": text[root_command_start:start],
               "root_command_start_char": root_command_start, "root_command_start_byte": byte(root_command_start),
               "mutual_context": any(kind == "mutual" for kind, _ in frames),
               "version_info": [{toolchain.split(":")[-1]: revision}], "revision": revision,
               "file_sha256": file_hash, "src_sha256": sha(span["src"]), "proof_sha256": sha(span["proof"]),
               "contains_sorry": incomplete, "native_parser_complete": False, "extraction_method": "lexical_layout",
               "compile_status": "not_checked_by_extractor", "axioms": None, "heartbeat": None, "heartbeat_status": "not_measured",
               "approximate_tactic_heads": counts(span["proof"])}
        if incomplete:
            row["exclusion_reason"] = "explicit_sorry_or_admit_in_source_proof"
        elif not assignment:
            row["exclusion_reason"] = "non_assignment_value_requires_special_replacement"
        # Mechanical equality verifies source preservation, not semantic validity.
        assert text[start:proof_start] + row["proof"] == row["src"]
        assert text[:proof_start] + row["proof"] + text[end:] == text
        records.append(row)
    return records, unresolved, len(candidates)


def extract(args):
    repo, out = args.repo.resolve(), args.out.resolve()
    revision = git(repo, "rev-parse", args.revision + "^{commit}").decode().strip()
    config_path = ROOT / "data/remaining_sources.json"
    config = json.loads(config_path.read_text()).get("sources", {}).get(args.source, {}) if config_path.exists() else {}
    if config.get("revision") != revision:
        config = {}
    tracked = sorted(p for p in git(repo, "ls-tree", "-r", "--name-only", revision).decode().splitlines() if p.endswith(".lean"))
    out.mkdir(parents=True, exist_ok=True)
    toolchain = ""
    tree = set(git(repo, "ls-tree", "-r", "--name-only", revision).decode().splitlines())
    for filename in sorted(tree):
        if ("/" not in filename and (filename.startswith("LICENSE") or filename in {"lean-toolchain", "lakefile.lean", "lakefile.toml", "lake-manifest.json"})) or filename == config.get("toolchain_file") or filename == 'lean4/LICENSE':
            content = git(repo, "show", f"{revision}:{filename}")
            destination = out / "LICENSE" if filename == 'lean4/LICENSE' else out / filename if filename.startswith("LICENSE") else out / "environment" / filename
            destination.parent.mkdir(exist_ok=True, parents=True)
            destination.write_bytes(content)
            if filename.endswith("lean-toolchain"):
                toolchain = content.decode().strip()
    files, counts_all, kinds, styles = [], Counter(), Counter(), Counter()
    snapshot = ROOT / "data/arena_snapshot.json"
    warmups = {}
    if snapshot.exists():
        arena_revision = json.loads(snapshot.read_text())["arena_revision"]
        with (ROOT / "data/arena" / arena_revision / "benchmark_data_warmup.jsonl").open() as stream:
            for number, line in enumerate(stream, 1):
                warmup = json.loads(line)
                if warmup["source"] == args.source:
                    warmups[warmup["name"]] = (number, warmup)
    warmup_matches = []
    next_id = 1
    with ExitStack() as stack:
        streams = {name: stack.enter_context(gzip.open(out / "inventory.jsonl.gz", "wt", compresslevel=3) if args.compact and name == "inventory" else (out / (name + ".jsonl")).open("w")) for name in ["inventory", "benchmark", "equations", "structures", "excluded", "unresolved_declarations"]}
        index = stack.enter_context((out / "index.md").open("w"))
        index.write(f"# {args.source} extracted declarations\n\nLexical/layout candidates; compilation and heartbeat not checked.\n\n| ID | Declaration | File | Form |\n|---|---|---|---|\n")
        for file_number, file_path in enumerate(tracked, 1):
            if shutil.disk_usage(out).free < 2 * 1024 ** 3:
                raise RuntimeError("Stopped before disk free space falls below 2 GiB; extraction is incomplete")
            data = git(repo, "show", f"{revision}:{file_path}")
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError(f"Non-UTF8 tracked source: {file_path}") from error
            if len(data) > args.max_file_bytes:
                records, candidates = [], 0
                unresolved = [{"file_path": file_path, "reason": "file_exceeds_configured_byte_limit", "source_bytes": len(data), "file_sha256": sha(data), "scope": "whole_file_declaration_count_unknown"}]
            else:
                records, unresolved, candidates = extract_text(text, file_path, args.source, revision, toolchain, args.url)
                assert candidates == len(records) + len(unresolved)
            file_entry = {"file_path": file_path, "file_sha256": sha(data), "source_bytes": len(data), "lexical_declarations": candidates,
                          "declarations": len(records), "unresolved_declarations": len(unresolved)}
            files.append(file_entry)
            counts_all.update(files_scanned=1, files_with_declarations=bool(candidates), total_declarations=len(records), lexical_declarations=candidates, unresolved_declarations=len(unresolved), source_bytes=len(data))
            if candidates or unresolved:
                context = out / "context" / file_path
                context.parent.mkdir(parents=True, exist_ok=True)
                context.write_bytes(data)
            for issue in unresolved:
                streams["unresolved_declarations"].write(json.dumps(issue, ensure_ascii=False) + "\n")
            for row in records:
                row["id"] = f"{args.source}_{next_id:05d}"
                next_id += 1
                row["context_file"] = "context/" + file_path
                row["problem_dir"] = "problems/" + row["id"]
                row["source_link"] = f"{args.url}/blob/{revision}/{file_path}#L{row['start_line']}-L{row['end_line']}"
                if row["name"] in warmups:
                    number, warmup = warmups[row["name"]]
                    warmup_matches.append({"warmup_number": number, "id": row["id"], "name": row["name"],
                        "equal_fields": {key: row[key] == warmup[key] for key in ["src", "statement", "proof_length", "num_lines", "header"]}})
                if not args.compact:
                    materialize_row(out, row)
                line = json.dumps(row, ensure_ascii=False) + "\n"
                streams["inventory"].write(line)
                category = "excluded" if row["contains_sorry"] else "equations" if row["proof_style"] == "equations" else "structures" if row["proof_style"] == "structure" else "benchmark"
                streams[category].write(json.dumps({"id": row["id"], "inventory_line": next_id - 1, "row_reference": True, "contains_sorry": row["contains_sorry"]}) + "\n" if args.compact else line)
                counts_all[category] += 1
                kinds[row["declaration_kind"]] += 1
                styles[row["proof_style"]] += 1
                safe_name = row["name"].replace("|", "\\|")
                link = row['context_file'] if args.compact else row['problem_dir'] + '/reference.lean'
                index.write(f"| [{row['id']}]({link}) | `{safe_name}` | {file_path}:{row['declaration_line']} | {row['proof_style']} |\n")
            if file_number % 250 == 0:
                print(json.dumps({"progress": args.source, "files": file_number, "files_total": len(tracked), "declarations": counts_all['total_declarations'], "unresolved": counts_all['unresolved_declarations']}), flush=True)
    manifest = {"source": args.source, "url": args.url, "revision": revision, "toolchain": toolchain,
                "revision_basis": config.get("revision_basis", "explicit_pinned_revision"),
                **dict(counts_all), "declaration_kinds": dict(kinds), "proof_styles": dict(styles),
                "extraction_methods": {"lexical_layout": counts_all["total_declarations"]}, "native_parser_complete": False,
                "source_scope": "all tracked .lean files in pinned Git tree, including tests/examples/problems/solutions; no fetched dependencies", "compact": args.compact,
                "inventory_file": "inventory.jsonl.gz" if args.compact else "inventory.jsonl", "subset_format": "inventory_line_references" if args.compact else "full_records", "max_file_bytes": args.max_file_bytes,
                "validation_scope": "Full-file exact original-proof reinsertion; lexical token partition. No Lean AST, elaboration, kernel, axioms or heartbeat validation.",
                "extractor_sha256": sha(Path(__file__).read_bytes()), "layout_parser_sha256": sha((ROOT / "scripts/physlib_layout.py").read_bytes()),
                "lexical_parser_sha256": sha((ROOT / "scripts/physlib_lexical.py").read_bytes())}
    dump(out / "files.json", files)
    dump(out / "warmup_matches.json", {"checks": warmup_matches, "missing_names": sorted(set(warmups) - {r['name'] for r in warmup_matches}), "note": "PutnamBench source repository and Arena standalone reference proofs are different datasets" if args.source == "putnambench" else "Exact source-field comparison only; not kernel validation"})
    dump(out / "manifest.json", manifest)
    dump(out / "status.json", {"state": "lexical_extraction_complete", "unresolved_declarations": counts_all["unresolved_declarations"], "compile_status": "not_run", "heartbeat_status": "not_measured"})
    (out / "README.md").write_text(f"# {args.source} 추출 결과\n\n출처: {args.url}, 커밋 `{revision}`, 도구 버전 `{toolchain}`.\n\n"
        f"Git에 포함된 Lean 파일 {len(files):,}개를 한 파일씩 읽어 정리 {counts_all['total_declarations']:,}개를 분리했습니다. 미분리/모호한 키워드 후보 {counts_all['unresolved_declarations']:,}개는 `unresolved_declarations.jsonl`에 보존했습니다.\n\n"
        "## 범위와 검증 한계\n\n전체 행은 `extraction_method=lexical_layout`, `native_parser_complete=false`입니다. Python으로 주석·문자열·syntax quotation을 마스킹하고 정리 시작, 명제/증명 구분, 다음 명령의 들여쓰기를 분석했습니다. 완전한 Lean 파서가 아니므로 사용자 정의 문법, 이름 해석 및 증명 경계는 추가 검증이 필요합니다. 모든 추출 행의 원문 재삽입은 정확히 일치합니다. 이 검사는 문법·증명 유효성을 보장하지 않습니다. Lean 실행·컴파일·공리 검증·heartbeat 측정은 하지 않았습니다.\n\n"
        "`inventory.jsonl`은 `sorry`가 있는 행도 포함합니다. `benchmark.jsonl`은 직접 `sorry/admit`가 없는 대입형 후보이며 검증된 벤치마크가 아닙니다. 방정식형/구조체형은 `equations.jsonl`/`structures.jsonl`, 직접 미완성 증명은 `excluded.jsonl`에 있습니다. 모든 tracked 파일을 포함하여 문제와 풀이, 예제와 테스트는 중복될 수 있습니다.\n\n"
        "각 `problems/<id>/`에는 `reference.lean`, `statement.lean`, `proof.lean`, `metadata.json`이 있습니다. 원본 파일 문맥은 `context/`, 환경 고정 파일은 `environment/`에 보존합니다. 정리 목록은 [index.md](index.md), 파일별 범위는 `files.json`, 수량·해시는 `manifest.json`을 참조하세요.\n\n"
        + ("대규모 코퍼스용 compact 모드입니다. `inventory.jsonl.gz`만 전체 레코드를 담고 나머지 subset JSONL은 id와 inventory_line 참조입니다. 개별 문제 파일은 필요할 때 `python3 scripts/extract_remaining.py --out " + str(out) + " --materialize ID`로 생성합니다.\n\n" if args.compact else "") +
        f"재생성: `python3 scripts/extract_remaining.py --source {args.source} --repo sources/{args.source} --revision {revision} --url {args.url} --out {args.source}{' --compact' if args.compact else ''}`\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def materialize_row(out, row):
    folder = out / row["problem_dir"]
    folder.mkdir(parents=True, exist_ok=True)
    for filename, key in [("reference.lean", "src"), ("statement.lean", "statement"), ("proof.lean", "proof")]:
        (folder / filename).write_text(row[key])
    dump(folder / "metadata.json", {k: v for k, v in row.items() if k not in {"src", "statement", "proof"}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--url", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compact", action="store_true", help="Full inventory, reference-only subsets, on-demand problem files")
    parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    parser.add_argument("--materialize", metavar="ID")
    args = parser.parse_args()
    if args.materialize:
        path = args.out / "inventory.jsonl"
        stream = path.open() if path.exists() else gzip.open(args.out / "inventory.jsonl.gz", "rt")
        with stream:
            for line in stream:
                row = json.loads(line)
                if row["id"] == args.materialize:
                    materialize_row(args.out, row)
                    return
        parser.error("ID not present in inventory")
    if not all([args.source, args.repo, args.revision]):
        parser.error("extraction requires --source, --repo, --revision")
    extract(args)


if __name__ == "__main__":
    main()
