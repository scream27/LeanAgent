"""Layout boundary regressions and conservative extraction coverage (no Lean jobs)."""
import collections
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from physlib_layout import Layout
from physlib_lexical import declaration_positions
import extract_physlib as extraction


def span(text):
    start = declaration_positions(text)[0]
    node = {'declaration_range': {'start_byte': len(text[:start].encode())},
            'root_command_range': {'start_byte': 0}}
    return Layout(text).extract(node)


class LayoutTests(unittest.TestCase):
    def test_header_let_default_and_absolute_value(self):
        text = 'lemma f (n : Nat := 0) :\n  let x := n;\n  |x| = |n| := by rfl\n\nalias g := f\n'
        row = span(text)
        self.assertEqual(row['proof'], ' by rfl')
        self.assertTrue(row['statement'].endswith('|x| = |n|'))
        self.assertTrue(row['src'].endswith('by rfl'))

    def test_lambda_patterns_inside_statement(self):
        text = 'lemma f : id = fun\n    | 0 => 0\n    | n+1 => n+1 := by rfl\n'
        self.assertEqual(span(text)['proof'], ' by rfl')

    def test_equations_following_lambda_in_type(self):
        text = 'lemma f : (n : Nat) →\n    id = fun x => x\n  | 0 => by rfl\n  | n+1 => by\n    obtain h := True.intro\n    rfl\n\nadd_aesop_rules safe norm [f]\n'
        row = span(text)
        self.assertEqual(row['value_style'], 'equations')
        self.assertTrue(row['proof'].startswith('| 0 =>'))
        self.assertTrue(row['proof'].endswith('rfl'))

    def test_comments_strings_and_following_command(self):
        text = '/-- lemma ghost := --/\nlemma f : True := by\n  /- nested /- end Ghost -/ comment -/\n  let s := "end Ghost :="\n  trivial -- trailing comment\n\nmeta def tool := 0\n'
        row = span(text)
        self.assertTrue(row['src'].startswith('lemma f'))
        self.assertTrue(row['proof'].endswith('trivial'))

    def test_tuple_with_absolute_value(self):
        text = 'lemma f : (fun x => ⟨|x|, -|x|⟩) = f := by rfl\n'
        self.assertEqual(span(text)['proof'], ' by rfl')

    def test_project_bra_ket_notation(self):
        text = 'lemma f (m n : Fin 3) : ⟨m|n⟩ = 0 := by simp\n'
        self.assertEqual(span(text)['proof'], ' by simp')

    def test_project_ket_and_operator_notation(self):
        text = 'lemma f (m n p : Fin 3) :\n    |m⟩⟨n| |p⟩ = if n = p then |m⟩ else 0 := by\n  simp\n'
        self.assertEqual(span(text)['proof'], ' by\n  simp')


class CorpusTests(unittest.TestCase):
    def test_native_calibration_and_warmups(self):
        report = json.loads((ROOT / 'physlib/layout_validation.json').read_text())
        self.assertEqual(report['compared'], 6755)
        self.assertEqual(report['matched'], 6755)
        matches = json.loads((ROOT / 'physlib/warmup_matches.json').read_text())['checks']
        self.assertEqual(len(matches), 3)
        for row in matches:
            self.assertEqual(len(row['equal_fields']), 5)
            self.assertTrue(all(row['equal_fields'].values()))

    def test_all_declarations_accounted_for_and_reinsert_exactly(self):
        rows = extraction.read_jsonl(ROOT / 'physlib/inventory.jsonl')
        unresolved = extraction.read_jsonl(ROOT / 'physlib/unresolved_declarations.jsonl')
        actual = collections.Counter((r['file_path'], r['declaration_start_byte']) for r in rows + unresolved)
        expected = collections.Counter()
        texts = {}
        for file in json.loads((ROOT / 'physlib/files.json').read_text()):
            path = file['file_path']
            texts[path] = (ROOT / 'sources/physlib' / path).read_text()
            expected.update((path, len(texts[path][:p].encode())) for p in declaration_positions(texts[path]))
        self.assertEqual(actual, expected)
        self.assertEqual(sum(actual.values()), 9008)
        for row in rows:
            source = texts[row['file_path']]
            self.assertEqual(extraction.replace_proof(source, row, row['proof']), source, row['id'])
            self.assertEqual((ROOT / 'physlib' / row['problem_dir'] / 'reference.lean').read_text(), row['src'])
            if row['extraction_method'] == 'layout_with_native_start_anchor':
                self.assertFalse(row['native_parser_complete'])
                self.assertEqual(row['compile_status'], 'not_checked_by_extractor')


if __name__ == '__main__':
    unittest.main()
