"""Submission-integrity checks; no network, Lean installation or upload."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('exporter', ROOT / 'scripts/export_warmup_submission.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class SubmissionTests(unittest.TestCase):
    def test_current_team_p12_requires_explicit_fallback(self):
        with self.assertRaisesRegex(ValueError, 'expected the exact benchmark statement'):
            exporter.build_bundle()

    def test_bundle_preserves_every_selected_source(self):
        payload, audit = exporter.build_bundle(p12_reference=True)
        rows = [json.loads(line) for line in payload.decode().splitlines()]
        self.assertEqual(len(rows), 15)
        self.assertEqual(len({r['name'] for r in rows}), 15)
        self.assertTrue(all(set(r) == {'name', 'proof'} for r in rows))
        manifest = json.loads((ROOT / 'submissions/warmup/manifest.json').read_text())
        benchmark = {r['name']: r for r in map(json.loads, (ROOT / manifest['benchmarkSnapshot']).read_text().splitlines())}
        for entry, row in zip(manifest['problems'], rows):
            self.assertEqual(row['name'], entry['name'])
            expected = (benchmark[row['name']]['src'] if entry['id'] == 12 else
                        (ROOT / 'submissions/warmup' / entry['path']).read_text())
            self.assertEqual(row['proof'], expected)
        self.assertEqual(audit['problems'][11]['selection'], 'official_reference_fallback')
        self.assertFalse(audit['officiallySubmitted'])
        self.assertIsNone(audit['officialEvaluationPassed'])

    def test_intake_rejects_execution_but_allows_nested_comments(self):
        meta = {'name': 'x', 'statement': 'theorem x : True'}
        exporter.validate_proof('theorem x : True := by /- outer /- #eval -/ sorry -/ trivial', meta)
        for suffix in ('\n#eval IO.println "x"', '\nnative_decide', '\nsorry'):
            with self.assertRaisesRegex(ValueError, 'forbidden pattern'):
                exporter.validate_proof('theorem x : True := by trivial' + suffix, meta)

    def test_extra_helpers_and_changed_statement_rejected(self):
        meta = {'name': 'x', 'statement': 'theorem x : True'}
        for proof in ('theorem x : False := by trivial',
                      'theorem x : True := by trivial\nprivate lemma helper : True := by trivial',
                      'theorem x : True := by trivial\nprivate def helper := 0'):
            with self.assertRaises(ValueError):
                exporter.validate_proof(proof, meta)

    def test_tampered_best_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = root / 'submissions/warmup'; folder.mkdir(parents=True)
            original = json.loads((ROOT / 'submissions/warmup/manifest.json').read_text())
            original['benchmarkSnapshot'] = str(ROOT / original['benchmarkSnapshot'])
            (folder / 'manifest.json').write_text(json.dumps(original))
            for entry in original['problems']:
                dest = folder / entry['path']; dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / 'submissions/warmup' / entry['path']).read_bytes())
            best = folder / original['problems'][0]['path']
            best.write_text(best.read_text() + '\n')
            with self.assertRaisesRegex(ValueError, 'Best proof hash differs'):
                exporter.build_bundle(root, p12_reference=True)


if __name__ == '__main__':
    unittest.main()
