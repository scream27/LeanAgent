import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from compare_all_sources import collect, read_rows, warmup_references, ROOT


class AllSourcesTests(unittest.TestCase):
    def test_gzip_stream_and_sorry_denominator(self):
        def row(number, proof, sorry):
            return dict(id=str(number), source='test', name='test', file_path='Test.lean',
                        proof=proof, proof_sha256=hashlib.sha256(proof.encode()).hexdigest(),
                        proof_style='by', declaration_kind='lemma', contains_sorry=sorry,
                        extraction_method='lexical_layout')
        records = [row(1, 'by simp; simp', False), row(2, 'by sorry', True)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'inventory.jsonl.gz'
            with gzip.open(path, 'wt') as output:
                output.write(''.join(json.dumps(r)+'\n' for r in records))
            self.assertEqual(list(read_rows(path)), records)
            result = collect(path, io.StringIO())
        all_rows = result['subsets']['all']
        complete = result['subsets']['no_direct_sorry']
        self.assertEqual(all_rows['declarations'], 2)
        self.assertEqual(complete['declarations'], 1)
        self.assertEqual(all_rows['heads'][0]['occurrences'], 2)
        self.assertEqual(all_rows['heads'][0]['prevalence_percent'], 50)
        self.assertEqual(complete['heads'][0]['prevalence_percent'], 100)

    def test_no_complete_proofs_yields_empty_not_fake_zero_statistics(self):
        record = dict(id='p1', source='test', name='p1', file_path='P.lean',
                      proof='by sorry', proof_sha256=hashlib.sha256(b'by sorry').hexdigest(),
                      proof_style='by', declaration_kind='theorem', contains_sorry=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'inventory.jsonl'
            path.write_text(json.dumps(record)+'\n')
            result = collect(path, io.StringIO())
        self.assertEqual(result['subsets']['no_direct_sorry']['declarations'], 0)
        self.assertEqual(result['subsets']['no_direct_sorry']['heads'], [])

    def test_putnam_warmup_reference_is_separate_and_lossless(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, evidence = warmup_references(ROOT, Path(tmp))
            rows = list(read_rows(path))
        self.assertEqual(len(rows), 3)
        self.assertTrue(evidence)
        for row in rows:
            self.assertEqual(row['source'], 'putnambench_warmup')
            self.assertEqual(row['environment_hashes_are'], 'mathlib4_commits_not_putnambench_commits')
            self.assertFalse(row['contains_sorry'])
            self.assertTrue(row['src'].endswith(row['proof']))


if __name__ == '__main__':
    unittest.main()
