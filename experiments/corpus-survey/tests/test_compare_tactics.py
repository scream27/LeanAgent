"""Lightweight tests for source-only tactic comparison; no Lean imports."""
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from compare_tactics import Aggregate, category, collect, extended_heads, subset_names
from survey import tactic_heads


class CounterTests(unittest.TestCase):
    def test_nested_comments_and_literals_do_not_count(self):
        source = 'by\n /- simp /- rw -/ exact -/\n exact "simp\\\" rw"\n -- apply\n simp'
        self.assertEqual(Counter(h['tactic'] for h in extended_heads(source)), {'exact': 1, 'simp': 1})

    def test_boundary_and_combinator_occurrences(self):
        source = "by\n  first | exact h | simp\n  all_goals try rw [h]\n  cases x <;> simp only [f]"
        heads = extended_heads(source)
        self.assertEqual(Counter(h['tactic'] for h in heads), {'exact': 1, 'simp': 2, 'rw': 1, 'cases': 1})
        self.assertEqual([h['form'] for h in heads if 'form' in h], ['simp other', 'simp only'])

    def test_extended_heads_preserve_variant_and_unknown_omission(self):
        source = "by\n fun_prop\n refine' h\n convert! h\n unknown_custom\n fin_cases i\n ring_nf!"
        self.assertEqual([h['tactic'] for h in extended_heads(source)], ['fun_prop', "refine'", 'convert!', 'fin_cases', 'ring_nf!'])
        self.assertEqual(tactic_heads(source), [])

    def test_projection_not_counted_but_spaced_bullet_is(self):
        source = "by\n exact (h).right\n . right\n exact (f x).congr g"
        self.assertEqual(Counter(h['tactic'] for h in extended_heads(source)), {'exact': 2, 'right': 1})
        self.assertEqual(Counter(h['tactic'] for h in tactic_heads(source)), {'exact': 2, 'right': 2, 'congr': 1})

    def test_ambiguous_and_conv_categories(self):
        for name in ('rfl', 'let', 'have', 'decide', 'funext'):
            self.assertEqual(category(name), 'term_or_tactic')
        self.assertEqual(category('case'), 'branch_structure')
        self.assertEqual(category('enter'), 'conv_control')
        self.assertEqual(category('fun_prop'), 'tactic_candidate')

    def test_term_proof_can_contain_nested_tactics(self):
        self.assertEqual([h['tactic'] for h in extended_heads('fun x => by simp')], ['simp'])
        self.assertEqual([h['tactic'] for h in extended_heads('rfl')], ['rfl'])

    def test_simp_only_after_flags_and_config(self):
        source = 'by\n simp +contextual only [h]\n simp (disch := (fun_prop)) only [f]\n simp -zeta +beta only\n simp [g]'
        self.assertEqual([h['form'] for h in extended_heads(source) if 'form' in h], ['simp only','simp only','simp only','simp other'])
        self.assertEqual([h['form'] for h in tactic_heads(source) if 'form' in h], ['simp other']*4)

    def test_wrapper_and_nested_head_are_separately_classified(self):
        self.assertEqual([h['tactic'] for h in extended_heads('by with_unfolding_all decide')], ['with_unfolding_all','decide'])
        self.assertEqual(category('with_unfolding_all'), 'tactic_wrapper')
        self.assertEqual(category('solve'), 'tactic_wrapper')


class AggregateTests(unittest.TestCase):
    @staticmethod
    def record(proof=' by\n simp\n simp\n rw [h]', **extra):
        return dict(id='unit_1', source='unit', name='test', file_path='A.lean', source_link='https://example.invalid',
                    proof=proof, proof_sha256=hashlib.sha256(proof.encode()).hexdigest(),
                    proof_style='by', declaration_kind='theorem', contains_sorry=False,
                    native_parser_complete=True, version_info=[{'v1':'sha'}], **extra)

    def test_repeated_heads_and_zero_hits_use_all_denominator(self):
        agg = Aggregate()
        one = self.record()
        two = self.record(' some_term')
        agg.add(one, extended_heads(one['proof']))
        agg.add(two, extended_heads(two['proof']))
        result = agg.summary()
        heads = {x['name']: x for x in result['heads']}
        self.assertEqual(heads['simp']['occurrences'], 2)
        self.assertEqual(heads['simp']['declarations'], 1)
        self.assertEqual(heads['simp']['prevalence_percent'], 50)
        self.assertEqual(heads['simp']['occurrences_per_100_declarations'], 100)
        self.assertEqual(result['declarations_without_recognized_heads'], 1)
        self.assertEqual(result['cooccurrence'][0]['declarations'], 1)

    def test_subsets_do_not_confuse_direct_sorry_with_verification(self):
        row = self.record()
        self.assertEqual(set(subset_names(row, set())), {'all','by_style','no_direct_sorry','native_ast'})
        row['contains_sorry'] = True
        row['native_parser_complete'] = False
        self.assertEqual(set(subset_names(row, {'unit_1'})), {'all','by_style','layout_recovered','kernel_verified_strata'})

    def test_collect_preserves_baseline_and_proof_hash(self):
        row = self.record(' by fun_prop', approximate_tactic_heads={})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'inventory.jsonl'
            path.write_text(json.dumps(row) + '\n')
            output = io.StringIO()
            result = collect(path, set(), output)
            self.assertEqual(result['stored_counter_mismatches'], 0)
            self.assertEqual(result['subsets']['all']['head_occurrences'], 1)
            self.assertEqual(result['baseline_subsets']['all']['head_occurrences'], 0)
            self.assertEqual(json.loads(output.getvalue())['heads'], {'fun_prop': 1})
            row['proof_sha256'] = 'wrong'
            path.write_text(json.dumps(row) + '\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                collect(path, set(), io.StringIO())


if __name__ == '__main__':
    unittest.main()
