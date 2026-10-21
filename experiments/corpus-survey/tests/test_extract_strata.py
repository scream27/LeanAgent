"""Extraction invariants: preserve editable proof spans and real upstream context."""
import json
from pathlib import Path
import sys
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_strata as extraction


class ExtractionTests(unittest.TestCase):
    def extract(self, source):
        return extraction.extract_file(source, "Synthetic.lean")

    def assert_spans(self, source, records):
        for row in records:
            with self.subTest(name=row["name"]):
                self.assertEqual(source[row["start_char"]:row["end_char"]], row["src"])
                self.assertEqual(source[row["proof_start_char"]:row["end_char"]], row["proof"])
                self.assertEqual(source[row["proof_start_char"] - 2:row["proof_start_char"]], ":=")
                self.assertEqual(source[row["start_char"]:row["proof_start_char"] - 2].rstrip(), row["statement"])
                self.assertEqual(source.count("\n", 0, row["start_char"]) + 1, row["start_line"])
                self.assertEqual(source.count("\n", 0, row["end_char"] - 1) + 1, row["end_line"])

    def test_default_binders_are_not_proof_delimiters(self):
        source = "theorem foo (n : Nat := 0) (h : n = n := by rfl) : n = n := by\n  exact h\n"
        rows = self.extract(source)["records"]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["statement"].endswith(": n = n"))
        self.assertEqual(rows[0]["proof"].strip(), "by\n  exact h")
        self.assert_spans(source, rows)

    def test_nested_comments_and_strings_do_not_create_declarations(self):
        source = '''/- theorem ghost : True := by /- lemma nested : True := by -/ trivial -/
def text := "theorem fake : True := by sorry"
theorem real : True := by
  -- theorem fake_again : False := by sorry
  trivial
'''
        rows = self.extract(source)["records"]
        self.assertEqual([r["name"] for r in rows], ["real"])
        self.assert_spans(source, rows)

    def test_wrappers_and_attributes_stay_in_statement(self):
        source = '''namespace Outer
/-- A doc comment that must not become the declaration. -/
open Classical in
@[simp]
theorem foo : True := by trivial
omit [DecidableEq Nat] in
theorem bar : True := True.intro
end Outer
'''
        rows = self.extract(source)["records"]
        self.assertEqual([r["name"] for r in rows], ["Outer.foo", "Outer.bar"])
        self.assertEqual(rows[0]["statement"], "open Classical in\n@[simp]\ntheorem foo : True")
        self.assertTrue(rows[1]["statement"].startswith("omit [DecidableEq Nat] in\n"))
        self.assert_spans(source, rows)

    def test_sections_and_mutual_blocks_do_not_pop_namespace(self):
        source = '''namespace Outer
section Local
theorem a : True := True.intro
end Local
mutual
def f : Nat := 0
def g : Nat := 1
end
namespace Inner
private theorem b : True := by trivial
end Inner
theorem c : True := by trivial
end Outer
'''
        rows = self.extract(source)["records"]
        self.assertEqual([r["name"] for r in rows], ["Outer.a", "Outer.Inner.b", "Outer.c"])
        self.assert_spans(source, rows)

    def test_term_proofs_and_unicode_offsets(self):
        source = '''namespace α
theorem refl_term (β : Nat) : β = β := rfl
theorem identity : True → True := fun h => h
theorem match_term (n : Nat) : n = n :=
  match n with
  | 0 => rfl
  | Nat.succ _ => rfl
end α
'''
        rows = self.extract(source)["records"]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["proof_style"] == "term" for r in rows))
        self.assert_spans(source, rows)

    def test_incomplete_proofs_are_kept_separately(self):
        result = self.extract("theorem incomplete : True := by sorry\ntheorem complete : True := by trivial\n")
        self.assertEqual([r["name"] for r in result["records"]], ["complete"])
        self.assertEqual(len(result["excluded"]), 1)

    def test_recursive_proof_termination_clause_is_preserved(self):
        source = '''private theorem recurse (n : Nat) : n = n := by
  cases n with
  | zero => rfl
  | succ n => exact congrArg Nat.succ (recurse n)
  termination_by n

@[simp]
theorem next : True := by trivial
'''
        rows = self.extract(source)["records"]
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]["proof"].endswith("termination_by n"))
        self.assertNotIn("@[simp]", rows[0]["proof"])
        self.assert_spans(source, rows)

    def test_replacement_preserves_original_whitespace_and_rejects_wrong_source(self):
        source = "theorem tight : True :=by trivial\n"
        row = self.extract(source)["records"][0]
        self.assertEqual(extraction.replace_proof(source, row, row["proof"]), source)
        with self.assertRaises(ValueError):
            extraction.replace_proof(source + "\n", row, row["proof"])


@unittest.skipUnless((ROOT / "sources/strata").exists(), "pinned Strata sources not collected")
class PinnedCorpusTests(unittest.TestCase):
    assert_spans = ExtractionTests.assert_spans

    def test_cli_rejects_overwriting_dataset_or_source(self):
        proof = ROOT / "strata/problems/strata_0001/proof.lean"
        row = extraction.read_jsonl(ROOT / "strata/inventory.jsonl")[0]
        other = extraction.read_jsonl(ROOT / "strata/inventory.jsonl")[-1]
        targets = [ROOT / "strata/inventory.jsonl", ROOT / "strata" / other["context_file"],
                   proof, ROOT / "sources/strata" / row["file_path"]]
        for target in targets:
            with self.subTest(target=target):
                before = target.read_bytes()
                result = subprocess.run([sys.executable, str(ROOT / "scripts/extract_strata.py"),
                                         "replace", "--id", row["id"], "--proof", str(proof),
                                         "--output", str(target)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Write the candidate outside", result.stderr)
                self.assertEqual(target.read_bytes(), before)

    def test_all_source_spans_are_lossless(self):
        files = sorted((ROOT / "sources/strata").rglob("*.lean"))
        self.assertEqual(len(files), 377)
        rows_all = []
        excluded_all = []
        for path in files:
            source = path.read_text()
            result = extraction.extract_file(source, str(path.relative_to(ROOT / "sources/strata")))
            rows_all.extend(result["records"])
            excluded_all.extend(result["excluded"])
            self.assert_spans(source, result["records"])
            for row in result["records"] + result["excluded"]:
                self.assertEqual(extraction.replace_proof(source, row, row["proof"]), source, row["name"])
        # Independent masked lexical inventory: 615 actual theorem declarations.
        self.assertEqual(len(rows_all) + len(excluded_all), 615)
        call_elim = [r for r in rows_all + excluded_all if r["file_path"] == "Strata/Transform/CallElimCorrect.lean"]
        self.assertEqual(len(call_elim), 127)

    def test_warmup_1_to_3_declarations_and_statements_match(self):
        paths = list((ROOT / "data/arena").glob("*/benchmark_data_warmup.jsonl"))
        if not paths:
            self.skipTest("official warmup snapshot not collected")
        warmups = [json.loads(line) for line in paths[0].read_text().splitlines() if line.strip()][:3]
        for warmup in warmups:
            source = (ROOT / "sources/strata" / warmup["file_path"]).read_text()
            records = extraction.extract_file(source, warmup["file_path"])["records"]
            found = [r for r in records if r["name"] == warmup["name"]]
            self.assertEqual(len(found), 1, warmup["name"])
            self.assertEqual(found[0]["src"], warmup["src"])
            self.assertEqual(found[0]["statement"], warmup["statement"])


if __name__ == "__main__":
    unittest.main()
