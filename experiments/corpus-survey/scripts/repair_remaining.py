#!/usr/bin/env python3
"""Apply explicitly reviewed source-span overrides to a compact extraction.

No generalized syntax heuristic is added: each override is tied to a pinned
source hash and exact character offsets, preserving the baseline parser audit.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import zlib

from extract_remaining import sha, dump, mask_noncode, IDENT, MODIFIERS
from survey import counts
import proof_tokens


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def reviewed_record(out, item, manifest):
    text = (out / item['context_file']).read_text()
    assert sha(text) == item['file_sha256']
    start, end, delimiter, proof_start = [item[k] for k in ['start_char', 'end_char', 'delimiter_start_char', 'proof_start_char']]
    assert 0 <= start <= delimiter <= proof_start < end <= len(text)
    src, statement, proof = text[start:end], text[start:delimiter].rstrip(), text[proof_start:end]
    assert sha(src) == item['src_sha256'] and sha(proof) == item['proof_sha256']
    assert text[:proof_start] + proof + text[end:] == text
    keyword = len(text.encode()[:item['declaration_start_byte']].decode())
    root_start = start
    prefix = mask_noncode(text[start:keyword])
    if re.match(r'(?:set_option|open|include|omit|attribute)\b', prefix):
        wrappers = list(re.finditer(r'\bin\b', prefix))
        if wrappers:
            after_wrapper = start + wrappers[-1].end()
            first = re.search(r'\S', mask_noncode(text[after_wrapper:keyword + 7]))
            start = after_wrapper + first.start()
            src, statement = text[start:end], text[start:delimiter].rstrip()
    declaration_kind = re.match(r'lemma|theorem', text[keyword:])[0]
    name = re.match(r'\s*(' + IDENT + r')', text[keyword + len(declaration_kind):])[1]
    ns = item['name'][:-len(name)].rstrip('.')
    assignment = item['value_style'] == 'assignment'
    assert (text[delimiter:proof_start] == ':=') if assignment else text[proof_start] == '|'
    style = ('by' if re.match(r'\s*by\b', mask_noncode(proof)) else 'term') if assignment else 'equations'
    incomplete = bool(re.search(r'\b(?:sorry|admit|sorryAx)\b', mask_noncode(proof)))
    byte = lambda pos: len(text[:pos].encode())
    row = dict(name=item['name'], local_name=name, namespace=ns.split('.') if ns else [], source=manifest['source'],
               name_resolution='syntactic_namespace_qualified_not_kernel_resolved', file_path=item['file_path'],
               src=src, statement=statement, proof=proof, proof_style=style, value_style=item['value_style'],
               declaration_kind=declaration_kind, start_char=start, end_char=end,
               proof_start_char=proof_start, delimiter_start_char=delimiter,
               start_byte=byte(start), end_byte=byte(end), proof_start_byte=byte(proof_start),
               value_start_byte=byte(delimiter), value_end_byte=byte(end),
               declaration_start_byte=item['declaration_start_byte'],
               start_line=text.count('\n', 0, start)+1, end_line=text.count('\n', 0, end-1)+1,
               declaration_line=item['declaration_line'], num_lines=len(src.splitlines()),
               root_command_start_char=root_start, root_command_start_byte=byte(root_start),
               proof_length=proof_tokens.proof_length(src, statement) if assignment else None,
               proof_length_method='warmup_calibrated_appendix_J' if assignment else 'not_defined_for_non_assignment',
               modifiers=re.findall(r'\b(' + MODIFIERS + r')\b', mask_noncode(text[start:keyword])),
               wrappers=text[root_start:start], mutual_context=False, header='', url=manifest['url'],
               revision=manifest['revision'], version_info=[{manifest['toolchain'].split(':')[-1]: manifest['revision']}],
               file_sha256=item['file_sha256'], src_sha256=sha(src), proof_sha256=sha(proof),
               contains_sorry=incomplete, native_parser_complete=False,
               extraction_method='reviewed_source_span_override', compile_status='not_checked_by_extractor',
               axioms=None, heartbeat=None, heartbeat_status='not_measured',
               approximate_tactic_heads=counts(proof), context_file=item['context_file'],
               original_extraction_failure=item['reason'], span_review_note=item['review_note'])
    if incomplete: row['exclusion_reason'] = 'explicit_sorry_or_admit_in_source_proof'
    elif not assignment: row['exclusion_reason'] = 'non_assignment_value_requires_special_replacement'
    return row


def refresh_reviewed_member(out):
    """Preserve the baseline gzip member and replace only reviewed rows."""
    manifest = json.loads((out / 'manifest.json').read_text())
    baseline = json.loads((out / 'manifest_before_span_review.json').read_text())
    spec = json.loads((out / 'reviewed_span_overrides.json').read_text())
    inventory = out / 'inventory.jsonl.gz'
    before_hash = file_hash(inventory)
    decoder = zlib.decompressobj(31)
    with inventory.open('rb') as stream:
        while not decoder.eof:
            chunk = stream.read(65536)
            assert chunk, 'Baseline gzip member is truncated'
            decoder.decompress(chunk)
        boundary = stream.tell() - len(decoder.unused_data)
        stream.seek(boundary)
        with gzip.GzipFile(fileobj=stream, mode='rb') as reviewed:
            previous_rows = [json.loads(line) for line in reviewed]
    assert len(previous_rows) == len(spec['overrides'])
    records = [reviewed_record(out, item, manifest) for item in spec['overrides']]
    invariant_fields = ['name', 'file_path', 'proof_sha256', 'proof_start_byte', 'end_byte',
                        'proof_style', 'contains_sorry', 'proof_length', 'declaration_start_byte']
    for row, previous in zip(records, previous_rows):
        for field in ['id', 'problem_dir', 'source_link']:
            row[field] = previous[field]
        assert all(row[field] == previous[field] for field in invariant_fields)
        assert row['proof'] == previous['proof']
    pending = out / 'inventory.review-refresh.jsonl.gz'
    digest = hashlib.sha256()
    with inventory.open('rb') as source, pending.open('wb') as target:
        remaining = boundary
        while remaining:
            chunk = source.read(min(1024 * 1024, remaining))
            assert chunk
            target.write(chunk); digest.update(chunk); remaining -= len(chunk)
    assert digest.hexdigest() == manifest['span_review']['before_inventory_sha256']
    with gzip.open(pending, 'at', compresslevel=3) as stream:
        for row in records: stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    after_hash = file_hash(pending)
    pending.replace(inventory)
    review = manifest['span_review']
    review.update(repair_script_sha256=file_hash(Path(__file__)), after_inventory_sha256=after_hash,
                  wrapper_policy='Outer command wrappers are preserved separately and in context; src/statement begin at the declaration, including attributes/modifiers')
    dump(out / 'manifest.json', manifest)
    dump(out / 'span_review_report.json', review)
    report = {'before_inventory_sha256': before_hash, 'after_inventory_sha256': after_hash,
              'baseline_gzip_member_bytes': boundary, 'proofs_unchanged': len(records),
              'invariant_fields': ['id', *invariant_fields],
              'wrapper_rows': [row['id'] for row in records if row['wrappers']],
              'subset_ids_and_counts_unchanged': True}
    dump(out / 'wrapper_consistency_report.json', report)
    print(json.dumps(report, indent=2))


def apply(out):
    manifest = json.loads((out / 'manifest.json').read_text())
    override_path = out / 'reviewed_span_overrides.json'
    override_hash = file_hash(override_path)
    if manifest.get('span_review', {}).get('overrides_sha256') == override_hash:
        print('Reviewed overrides already applied')
        return
    assert manifest['compact']
    assert shutil.disk_usage(out).free > 2 * 1024 ** 3
    spec = json.loads(override_path.read_text())
    assert spec['source_revision'] == manifest['revision']
    unresolved = [json.loads(line) for line in (out / 'unresolved_declarations.jsonl').read_text().splitlines()]
    key = lambda row: (row['file_path'], row['declaration_start_byte'])
    unresolved_keys = {key(row) for row in unresolved}
    assert len({key(row) for row in spec['overrides']}) == len(spec['overrides'])
    assert all(key(row) in unresolved_keys for row in spec['overrides'])
    records = [reviewed_record(out, row, manifest) for row in spec['overrides']]
    before = dict(manifest)
    inventory = out / 'inventory.jsonl.gz'
    before_inventory_hash = file_hash(inventory)
    pending = out / 'inventory.review-pending.jsonl.gz'
    shutil.copyfile(inventory, pending)
    subsets = {name: [] for name in ['benchmark', 'equations', 'structures', 'excluded']}
    with gzip.open(pending, 'at', compresslevel=3) as stream:
        for number, row in enumerate(records, manifest['total_declarations'] + 1):
            row['id'] = f"{manifest['source']}_{number:05d}"
            row['problem_dir'] = 'problems/' + row['id']
            row['source_link'] = f"{row['url']}/blob/{row['revision']}/{row['file_path']}#L{row['start_line']}-L{row['end_line']}"
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            category = 'excluded' if row['contains_sorry'] else 'equations' if row['proof_style'] == 'equations' else 'benchmark'
            subsets[category].append({'id': row['id'], 'inventory_line': number, 'row_reference': True, 'contains_sorry': row['contains_sorry']})
    repaired_keys = {key(row) for row in records}
    remaining = [row for row in unresolved if key(row) not in repaired_keys]
    files = json.loads((out / 'files.json').read_text())
    per_file = Counter(row['file_path'] for row in records)
    for row in files:
        count = per_file[row['file_path']]
        row['declarations'] += count
        row['unresolved_declarations'] -= count
        assert row['declarations'] + row['unresolved_declarations'] == row['lexical_declarations']
    manifest['total_declarations'] += len(records)
    manifest['unresolved_declarations'] = len(remaining)
    for category, rows in subsets.items():
        manifest[category] = manifest.get(category, 0) + len(rows)
    for field, key_name in [('declaration_kinds', 'declaration_kind'), ('proof_styles', 'proof_style')]:
        value = Counter(manifest[field]); value.update(row[key_name] for row in records); manifest[field] = dict(value)
    manifest['extraction_methods']['reviewed_source_span_override'] = len(records)
    manifest['span_review'] = {'overrides_file': override_path.name, 'overrides_sha256': override_hash,
        'repair_script_sha256': file_hash(Path(__file__)), 'recovered_declarations': len(records),
        'before_inventory_sha256': before_inventory_hash, 'after_inventory_sha256': file_hash(pending),
        'scope': 'Explicitly reviewed, source-hash-pinned spans; no native AST, kernel or heartbeat verification'}
    assert manifest['total_declarations'] + len(remaining) == manifest['lexical_declarations']
    dump(out / 'manifest_before_span_review.json', before)
    shutil.copyfile(out / 'unresolved_declarations.jsonl', out / 'unresolved_before_span_review.jsonl')
    pending.replace(inventory)
    for category, rows in subsets.items():
        with (out / (category + '.jsonl')).open('a') as stream:
            for row in rows: stream.write(json.dumps(row) + '\n')
    with (out / 'index.md').open('a') as stream:
        for row in records:
            stream.write(f"| [{row['id']}]({row['context_file']}) | `{row['name']}` | {row['file_path']}:{row['declaration_line']} | {row['proof_style']} (reviewed span) |\n")
    (out / 'unresolved_declarations.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in remaining))
    dump(out / 'files.json', files)
    dump(out / 'manifest.json', manifest)
    dump(out / 'status.json', {'state': 'lexical_extraction_with_reviewed_spans_complete', 'unresolved_declarations': len(remaining), 'compile_status': 'not_run', 'heartbeat_status': 'not_measured'})
    dump(out / 'span_review_report.json', manifest['span_review'])
    print(json.dumps({'total_declarations': manifest['total_declarations'], 'recovered': len(records), 'unresolved': len(remaining)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--refresh-reviewed-member', action='store_true')
    args = parser.parse_args()
    if args.refresh_reviewed_member:
        refresh_reviewed_member(args.out)
    else:
        apply(args.out)
