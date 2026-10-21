import json
from collections import Counter
import unittest

from proof_length_distribution import ROOT, describe, quantile, public_calibration
from compare_all_sources import read_rows
from proof_tokens import proof_length


class ProofLengthDistributionTests(unittest.TestCase):
    def test_weighted_quantiles_and_empty_corpus(self):
        hist = Counter({1:2, 100:2})
        self.assertEqual(quantile(hist, .5), 50.5)
        self.assertEqual(quantile(hist, .9), 100)
        self.assertIsNone(describe(Counter())['p50'])
        self.assertEqual(describe(Counter())['bin_percent'], [None]*11)

    def test_nonoverlapping_bins_and_included_by(self):
        stats = describe(Counter([9,10,24,25,9999,10000]))
        self.assertEqual(stats['bin_counts'], [1,2,1,0,0,0,0,0,0,1,1])
        statement = 'theorem t : True'
        self.assertEqual(proof_length(statement+' := by /- ignored /- nested -/ -/ trivial', statement), 2)

    def test_all_warmups_and_public_signature_boundary_difference(self):
        revision=json.loads((ROOT/'data/arena_snapshot.json').read_text())['arena_revision']
        rows=list(read_rows(ROOT/'data/arena'/revision/'benchmark_data_warmup.jsonl'))
        result=public_calibration(rows)
        self.assertEqual(result['known_boundary_matches'],15)
        self.assertEqual(result['current_public_matches'],14)
        self.assertEqual(result['rows'][10]['published'],1906)
        self.assertEqual(result['rows'][10]['current_public_function'],2219)
