#!/usr/bin/env python3
"""Compare lexical proof boundaries with saved native Strata/PhysLib ranges.

Runs Python only. Matching source spans do not establish Lean elaboration.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from extract_remaining import extract_text

from arena_workspace import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/remaining_sources/native_calibration.json')
    args = parser.parse_args()
    report = {'compared': 0, 'proof_matched': 0, 'mismatches': [], 'missing': [],
              'inputs': {}, 'extractor_sha256': hashlib.sha256((ROOT / 'scripts/extract_remaining.py').read_bytes()).hexdigest(),
              'scope': 'Exact proof string comparison against existing complete native AST spans; no Lean execution'}
    for source in ('strata', 'physlib'):
        by_file = defaultdict(list)
        path = ROOT / source / 'inventory.jsonl'
        report['inputs'][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open() as stream:
            for line in stream:
                row = json.loads(line)
                if row['native_parser_complete']:
                    by_file[row['file_path']].append(row)
        for file, known in by_file.items():
            text = (ROOT / source / 'context' / file).read_text()
            records, unresolved, _ = extract_text(text, file, source, 'calibration')
            actual = {r['declaration_line']: r for r in records}
            for row in known:
                report['compared'] += 1
                key = {'source': source, 'file_path': file, 'name': row['name'], 'line': row['declaration_line']}
                if row['declaration_line'] not in actual:
                    issues = [r for r in unresolved if r['declaration_line'] == row['declaration_line']]
                    report['missing'].append({**key, 'reasons': [r['reason'] for r in issues]})
                elif actual[row['declaration_line']]['proof'] != row['proof']:
                    a, b = actual[row['declaration_line']]['proof'], row['proof']
                    report['mismatches'].append({**key, 'expected_start': b[:120], 'actual_start': a[:120],
                                                 'expected_end': b[-150:], 'actual_end': a[-150:]})
                else:
                    report['proof_matched'] += 1
        print(source, 'checked', flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print({k: len(v) if isinstance(v, list) else v for k, v in report.items() if k != 'inputs'})
    if report['mismatches']:
        raise SystemExit('Proof boundary mismatch detected')


if __name__ == '__main__':
    main()
