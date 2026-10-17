import tempfile
import unittest
from pathlib import Path
from .common import sha, write, save
from .mining import mask_comments
from .verification import classify, safety, splice
from .generation import submit, prepare
from .report import stats, summarize


class PipelineTests(unittest.TestCase):
    def test_nested_comment_offsets_and_quoted_dash(self):
        text = 'theorem a : True := by /- one /- nested -/ two -/ trivial\n-- tail\n'
        masked = mask_comments(text)
        self.assertEqual(len(text), len(masked))
        self.assertEqual(text.count('\n'), masked.count('\n'))
        self.assertNotIn('nested', masked)
        self.assertIn('"--"', mask_comments('"--"'))

    def test_only_proof_changes_and_span_tampering_rejected(self):
        source = 'import A\ntheorem a : True := by trivial\ntheorem b : True := a\n'
        a = source.index('by trivial')
        row = dict(proof_start=a, proof_end=a+10, reference_proof='by trivial', source_sha256=sha(source))
        updated = splice(source, row, 'by exact True.intro')
        self.assertEqual(updated[:a], source[:a])
        self.assertTrue(updated.endswith('\ntheorem b : True := a\n'))
        with self.assertRaises(ValueError): splice(source+' ', row, 'by trivial')

    def test_safety_and_error_categories_are_separate(self):
        self.assertFalse(safety('by exact missing_lemma', 'Target'))
        self.assertEqual(classify('unknown identifier missing_lemma'), 'unknown_identifiers')
        self.assertTrue(safety('by exact sorryAx _ true', 'Target'))
        self.assertTrue(safety('by trivial\naxiom bad : False', 'Target'))
        self.assertTrue(safety('by trivial\nopen Classical', 'Target'))
        self.assertTrue(safety('by trivial\nvariable (x : Nat)', 'Target'))
        self.assertTrue(safety('by exact Target', 'Target'))
        self.assertFalse(safety('by /- sorry is prohibited -/ trivial', 'Target'))
        self.assertEqual(classify('unsolved goals'), 'unsolved_goals')
        self.assertEqual(classify('', timed_out=True), 'resource_exhaustion')
        self.assertEqual(classify('error: `grind` failed'), 'tactic_failures')
        self.assertEqual(classify('error: omega could not prove the goal'), 'tactic_failures')
        self.assertEqual(classify('error: Case tag `ftvar` not found.'), 'tactic_failures')

    def test_first_response_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            root = Path(tmp)
            save(root/'generation'/'p-1'/'request.json', {'candidate_id': 'p-1'})
            write(root/'proof.txt', 'by exact missing')
            submit(root, 'p-1', root/'proof.txt')
            write(root/'proof.txt', 'by trivial')
            with self.assertRaises(FileExistsError): submit(root, 'p-1', root/'proof.txt')
            self.assertEqual((root/'generation'/'p-1'/'response.txt').read_text(), 'by exact missing')

    def test_null_statistics_are_not_zero(self):
        self.assertIsNone(stats([])['mean'])
        self.assertEqual(stats([None, 2, 4])['mean'], 3)
        self.assertEqual(stats([2, 4])['standard_deviation'], 1)
        self.assertIsNone(summarize([])['compile_percentage'])

    def test_remaining_requires_pilot(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            write(Path(tmp)/'theorems.jsonl', '{}\n'*10)
            with self.assertRaises(FileNotFoundError): prepare(tmp, 'remaining')


if __name__ == '__main__': unittest.main()
