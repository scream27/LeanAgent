import unittest
from collections import Counter

from select_warmup_candidates import cutoff_top5, membership, review_key


class CandidateSelectionTests(unittest.TestCase):
    def test_boundary_ties_are_kept(self):
        self.assertEqual(cutoff_top5(Counter({1:17, 100:3})), (100,1,3))
        self.assertEqual(cutoff_top5(Counter(range(1,22))), (20,2,2))
        self.assertEqual(cutoff_top5(Counter()), (None,0,0))

    def test_two_independent_thresholds_and_excluded_proofs(self):
        row = {'proof_style':'by','contains_sorry':False,'proof_length':200}
        self.assertEqual(membership(row,151), ['ge200','top5pct'])
        self.assertEqual(membership(row,505), ['ge200'])
        self.assertEqual(membership({**row,'proof_length':180},151), ['top5pct'])
        self.assertEqual(membership({**row,'contains_sorry':True},151), [])
        self.assertEqual(membership({**row,'proof_style':'term'},151), [])

    def test_review_prefers_intersection_then_length_similarity(self):
        rows = [dict(id='A',both_sets=False,nearest_warmup_log_distance=0,proof_length=190),
                dict(id='B',both_sets=True,nearest_warmup_log_distance=1,proof_length=500),
                dict(id='C',both_sets=True,nearest_warmup_log_distance=.1,proof_length=220)]
        self.assertEqual([r['id'] for r in sorted(rows,key=review_key)], ['C','B','A'])
