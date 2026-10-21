import unittest
import json
from pathlib import Path
from extract_remaining import extract_text, mask_noncode


class LayoutExtractionTests(unittest.TestCase):
    def extract(self, source):
        return extract_text(source, 'Test.lean', 'test', 'abc', 'v4.32.0')

    def test_comments_strings_and_quotation(self):
        text = '''/- theorem ghost : False := by sorry /- nested -/ -/
def text := "theorem other : False := by sorry"
macro "foo" : command => `(theorem fake : True := by trivial)
theorem real : True := by trivial
'''
        rows, unresolved, count = self.extract(text)
        self.assertEqual((len(rows), len(unresolved), count), (1, 0, 1))
        self.assertEqual(rows[0]['name'], 'real')

    def test_namespaces_wrappers_modifiers(self):
        text = '''namespace A
section s
set_option maxRecDepth 100 in
@[simp]
private theorem foo : True := by trivial
end s
protected lemma bar : True := by exact foo
end A
theorem _root_.baz : True := by trivial
'''
        rows, unresolved, _ = self.extract(text)
        self.assertFalse(unresolved)
        self.assertEqual([r['name'] for r in rows], ['A.foo', 'A.bar', 'baz'])
        self.assertTrue(rows[0]['src'].startswith('@[simp]'))
        self.assertTrue(rows[0]['wrappers'].startswith('set_option'))
        self.assertEqual(rows[0]['modifiers'], ['private'])

    def test_multiline_attribute_inline_wrapper(self):
        text = '''@[simp,
  grind =]
theorem abc : True := by trivial
set_option foo true in theorem defg : True := by trivial
'''
        rows, unresolved, _ = self.extract(text)
        self.assertFalse(unresolved)
        self.assertTrue(rows[0]['statement'].startswith('@[simp,'))
        self.assertTrue(rows[1]['statement'].startswith('theorem'))
        self.assertTrue(rows[1]['wrappers'].startswith('set_option'))

    def test_styles_and_sorry(self):
        text = '''theorem a : True := by sorry
theorem b : True := True.intro
theorem c : Nat → True
  | 0 => True.intro
  | _ + 1 => True.intro
theorem d : True where
'''
        rows, unresolved, _ = self.extract(text)
        self.assertEqual([r['proof_style'] for r in rows], ['by', 'term', 'equations', 'structure'])
        self.assertTrue(rows[0]['contains_sorry'])
        self.assertFalse(rows[1]['contains_sorry'])

    def test_utf8_names_and_reinsertion(self):
        text = '''namespace α
theorem «name with spaces» (x : ℕ) : x = x := by rfl
end α
'''
        rows, unresolved, _ = self.extract(text)
        self.assertFalse(unresolved)
        row = rows[0]
        self.assertEqual(row['name'], 'α.«name with spaces»')
        self.assertEqual(text.encode()[row['start_byte']:row['end_byte']].decode(), row['src'])
        self.assertFalse(row['native_parser_complete'])

    def test_unknown_prefix_is_preserved_unresolved(self):
        rows, unresolved, count = self.extract('custom theorem odd : True := by trivial\n')
        self.assertEqual((len(rows), len(unresolved), count), (0, 1, 1))

    def test_default_and_let_type_assignments(self):
        rows, unresolved, _ = self.extract('theorem t (x : Nat := 1) : (let y := x; y) = x := by rfl\n')
        self.assertFalse(unresolved)
        self.assertEqual(rows[0]['proof'].strip(), 'by rfl')

    def test_do_bind_in_proposition(self):
        rows, unresolved, _ = self.extract('theorem t : f = (do\n  let x ← a\n  return x) := by rfl\n')
        self.assertFalse(unresolved)
        self.assertEqual(rows[0]['proof'].strip(), 'by rfl')

    def test_mask_equivalence(self):
        from survey import mask_noncode as old_mask
        samples = [r'''theorem foo' : "str\\\"/-fake-/" = r##"raw\"-- theorem"## := by rfl''',
                   "'a' '\\\\' '/-' /- hi /- nested -/ -/ -- theorem fake\ntheorem t := by trivial",
                   'namespace «theorem private»\ntheorem «a» : True := by trivial']
        for sample in samples:
            self.assertEqual(mask_noncode(sample), old_mask(sample))

    def test_public_section_scope(self):
        rows, unresolved, _ = self.extract('namespace A\npublic section\ntheorem x : True := by trivial\nend\ntheorem y : True := by trivial\nend A\n')
        self.assertEqual([r['name'] for r in rows], ['A.x', 'A.y'])
        rows, unresolved, _ = self.extract('theorem t : f = do\n  let x ← a\n  return x := by rfl\n')
        self.assertFalse(unresolved)
        self.assertEqual(rows[0]['proof'].strip(), 'by rfl')


class ReviewedSpanTests(unittest.TestCase):
    def test_pinned_overrides_preserve_original_spans(self):
        from repair_remaining import reviewed_record
        out = Path(__file__).resolve().parents[1] / 'leanpool'
        if not (out / 'reviewed_span_overrides.json').exists():
            self.skipTest('Pinned corpus not present')
        manifest = json.loads((out / 'manifest.json').read_text())
        overrides = json.loads((out / 'reviewed_span_overrides.json').read_text())['overrides']
        self.assertEqual(len(overrides), 19)
        for override in overrides:
            row = reviewed_record(out, override, manifest)
            text = (out / row['context_file']).read_text()
            self.assertEqual(text.encode()[row['start_byte']:row['end_byte']].decode(), row['src'])
            self.assertEqual(text.encode()[row['proof_start_byte']:row['end_byte']].decode(), row['proof'])
            self.assertFalse(row['native_parser_complete'])
            self.assertFalse(row['contains_sorry'])
            if row['name'] == 'psi_apply_complete_graph':
                self.assertIn('(ψ := φ)', row['statement'])
                self.assertTrue(row['proof'].lstrip().startswith('by'))

    def test_reviewed_wrappers_are_preserved_separately(self):
        from repair_remaining import reviewed_record
        out = Path(__file__).resolve().parents[1] / 'leanpool'
        if not (out / 'reviewed_span_overrides.json').exists():
            self.skipTest('Pinned corpus not present')
        manifest = json.loads((out / 'manifest.json').read_text())
        overrides = json.loads((out / 'reviewed_span_overrides.json').read_text())['overrides']
        rows = [reviewed_record(out, item, manifest) for item in overrides]
        wrapped = [row for row in rows if row['wrappers']]
        self.assertEqual(len(wrapped), 2)
        for row in wrapped:
            self.assertTrue(row['wrappers'].startswith('omit '))
            self.assertTrue(row['statement'].startswith('theorem '))
            self.assertLess(row['root_command_start_byte'], row['start_byte'])


if __name__ == '__main__':
    unittest.main()
