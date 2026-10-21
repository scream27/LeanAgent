#!/usr/bin/env python3
"""Check exported tactic counts and provenance without executing Lean."""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

from compare_tactics import sha256

from arena_workspace import ROOT


def main():
    folder = ROOT / 'results/all_sources'
    summary = json.loads((folder / 'summary.json').read_text())
    for path, expected in {**summary['inputs'], **summary['scripts']}.items():
        assert sha256(ROOT / path) == expected, path
    counts = Counter()
    occurrences = defaultdict(Counter)
    presence = defaultdict(Counter)
    with gzip.open(folder / 'declarations.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            subsets = ['all'] + ([] if row['contains_sorry'] else ['no_direct_sorry'])
            for subset in subsets:
                key = (row['source'], subset)
                counts[key] += 1
                occurrences[key].update(row['heads'])
                presence[key].update(row['heads'].keys())
    for source, data in summary['sources'].items():
        if 'manifest' in data:
            manifest = json.loads((ROOT / source / 'manifest.json').read_text())
            assert manifest == data['manifest'], source
            assert manifest['total_declarations'] == counts[(source, 'all')], source
        for subset in ['all', 'no_direct_sorry']:
            key = (source, subset)
            expected = data['subsets'][subset]
            assert counts[key] == expected['declarations'], key
            assert dict(occurrences[key]) == {h['name']: h['occurrences'] for h in expected['heads']}, key
            assert dict(presence[key]) == {h['name']: h['declarations'] for h in expected['heads']}, key
            assert sum(occurrences[key].values()) == expected['head_occurrences'], key
            for head in expected['heads']:
                assert head['prevalence_percent'] == round(100 * presence[key][head['name']] / counts[key], 4), key
    result = {
        'status': 'passed',
        'scope': 'Input/script SHA, current manifests, exported all/no_direct_sorry counts, occurrences, prevalence; not Lean or tactic-parser semantic validation',
        'declarations_by_source': {source: counts[(source, 'all')] for source in summary['sources']},
        'summary_sha256': sha256(folder / 'summary.json'),
        'declarations_sha256': sha256(folder / 'declarations.jsonl.gz'),
        'verification_script_sha256': sha256(Path(__file__)),
    }
    (folder / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
