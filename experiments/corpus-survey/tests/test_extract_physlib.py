"""Independent completeness checks and source-preserving Physlib edits."""
import collections
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_physlib as extraction
from physlib_lexical import declaration_positions


class LexicalInventoryTests(unittest.TestCase):
    def test_inline_attributes_modifiers_and_incomplete_headers(self):
        source = """@[simp, ext] private lemma α : True := by trivial
nonrec theorem beta : True := True.intro
@[simp]
protected theorem gamma : True := True.intro
private theorem broken (n : Nat) BAD UPSTREAM TEXT
"""
        self.assertEqual([source[p:].split()[1] for p in declaration_positions(source)],
                         ["α", "beta", "gamma", "broken"])

    def test_comments_strings_quotations_and_constructors_are_not_declarations(self):
        source = '''/- lemma ghost : True := /- theorem nested := -/ True.intro -/
def text := "lemma stringGhost : True := by sorry"
def syntaxData := `(command|
  theorem quotedGhost : True := by trivial)
inductive Kind where
  | def | lemma
def f := Kind.lemma
@[simp] lemma actual : True := by
  -- theorem lineGhost : False := by sorry
  trivial
'''
        self.assertEqual([source[p:].split()[1] for p in declaration_positions(source)], ["actual"])


class NativeExtractionTests(unittest.TestCase):
    def extract(self, source):
        return extraction.extract_file(source, "Synthetic.lean")

    def test_lemma_inline_attributes_nonrec_and_root_names(self):
        source = """namespace Outer.Inner
@[simp] private lemma α : True := by trivial
nonrec theorem beta : True := True.intro
protected theorem gamma : True := True.intro
lemma _root_.global : True := True.intro
end Outer.Inner
"""
        rows = self.extract(source)["records"]
        self.assertEqual([r["name"] for r in rows],
                         ["Outer.Inner.α", "Outer.Inner.beta", "Outer.Inner.gamma", "global"])
        self.assertEqual([r["declaration_kind"] for r in rows], ["lemma", "theorem", "theorem", "lemma"])
        self.assertIn("private", rows[0]["modifiers"])
        self.assertIn("nonrec", rows[1]["modifiers"])
        self.assertIn("protected", rows[2]["modifiers"])
        self.assertTrue(rows[0]["statement"].startswith("@[simp] private lemma"))

    def test_wrapped_unicode_default_binders_and_local_sections(self):
        source = """namespace α
section Local
/-- Documentation is not an editable statement. -/
set_option maxRecDepth 1000 in
open Classical in
@[simp]
lemma reflexive (β : Nat := 0) (h : β = β := by rfl) : β = β := by
  exact h
end Local
theorem next : True := True.intro
end α
"""
        rows = self.extract(source)["records"]
        self.assertEqual([r["name"] for r in rows], ["α.reflexive", "α.next"])
        self.assertTrue(rows[0]["statement"].startswith("set_option maxRecDepth"))
        self.assertTrue(rows[0]["statement"].endswith(": β = β"))
        self.assertEqual(rows[0]["proof"].strip(), "by\n  exact h")
        candidate = extraction.replace_proof(source, rows[0], " by rfl")
        self.assertEqual(candidate, source.replace("by\n  exact h", "by rfl"))
        self.assertEqual(extraction.replace_proof(source, rows[0], rows[0]["proof"]), source)
        with self.assertRaises(ValueError):
            extraction.replace_proof(source + "\n", rows[0], " by rfl")

    def test_quoted_command_is_not_extracted(self):
        source = """def quoted := `(command|
  theorem ghost : True := by trivial)
theorem real : True := by trivial
"""
        rows = self.extract(source)["records"]
        self.assertEqual([r["name"] for r in rows], ["real"])

    def test_direct_sorry_is_excluded_but_comment_is_not(self):
        source = """lemma incomplete : True := by sorry
lemma complete : True := by
  -- sorry is only a comment here
  trivial
"""
        result = self.extract(source)
        self.assertEqual([r["name"] for r in result["records"]], ["complete"])
        self.assertEqual([r["name"] for r in result["excluded"]], ["incomplete"])
        self.assertTrue(result["excluded"][0]["contains_sorry"])

    def test_equation_proofs_keep_termination_and_next_declaration(self):
        source = """theorem recursive : (n : Nat) → n = n
  | 0 => rfl
  | n + 1 => congrArg Nat.succ (recursive n)
termination_by n => n
decreasing_by exact Nat.lt_succ_self _

theorem following : True := True.intro
"""
        result = self.extract(source)
        equation = next(r for r in result["excluded"] if r["name"] == "recursive")
        self.assertEqual(equation["proof_style"], "equations")
        self.assertTrue(equation["proof"].endswith("decreasing_by exact Nat.lt_succ_self _"))
        self.assertEqual(extraction.replace_proof(source, equation, equation["proof"]), source)
        changed = extraction.replace_proof(source, equation, "by intro n; rfl")
        self.assertIn(":= by intro n; rfl\n\ntheorem following", changed)
        self.assertEqual([r["name"] for r in result["records"]], ["following"])


@unittest.skipUnless((ROOT / "sources/physlib/.git").exists(), "pinned source not collected")
class PinnedSourceTests(unittest.TestCase):
    def test_complete_tracked_file_and_independent_keyword_inventory(self):
        repo = ROOT / "sources/physlib"
        paths = subprocess.check_output(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", extraction.PHYSLIB_REV], text=True).splitlines()
        paths = [p for p in paths if p.endswith(".lean")]
        self.assertEqual(len(paths), 676)
        counts = collections.Counter()
        for path in paths:
            source = (repo / path).read_text()
            for offset in declaration_positions(source):
                counts[source[offset:].split()[0]] += 1
        self.assertEqual(dict(counts), {"lemma": 7437, "theorem": 1571})


@unittest.skipUnless((ROOT / "physlib/inventory.jsonl").exists(), "dataset not generated")
class PinnedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = extraction.read_jsonl(ROOT / "physlib/inventory.jsonl")

    def test_each_lexical_declaration_is_accounted_for_exactly_once(self):
        repo = ROOT / "sources/physlib"
        tracked = subprocess.check_output(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", extraction.PHYSLIB_REV], text=True).splitlines()
        expected = collections.Counter()
        for path in tracked:
            if not path.endswith(".lean"):
                continue
            source = (repo / path).read_text()
            for offset in declaration_positions(source):
                expected[path, len(source[:offset].encode())] += 1
        unresolved = extraction.read_jsonl(ROOT / "physlib/unresolved_declarations.jsonl")
        actual = collections.Counter((row["file_path"], row["declaration_start_byte"])
                                     for row in self.rows + unresolved)
        self.assertEqual(actual, expected)
        self.assertEqual(sum(actual.values()), 9008)
        corrupt = [r for r in self.rows + unresolved if r["file_path"] == "QuantumInfo/Regularized.lean"
                   and r["declaration_line"] == 131]
        self.assertEqual(len(corrupt), 1, "The suspicious upstream header must not be silently omitted")
        if "src" in corrupt[0]:
            self.assertIn("Expand commentComment on line R131Resolved", corrupt[0]["src"])
            self.assertEqual(corrupt[0]["compile_status"], "not_checked_by_extractor")

    def test_all_available_spans_and_context_are_lossless(self):
        sources = {}
        for row in self.rows:
            if row.get("proof_start_char") is None:
                continue
            path = row["file_path"]
            if path not in sources:
                original = (ROOT / "sources/physlib" / path).read_bytes()
                context = (ROOT / "physlib" / row["context_file"]).read_bytes()
                self.assertEqual(context, original, path)
                sources[path] = original.decode()
            source = sources[path]
            with self.subTest(name=row["name"]):
                self.assertEqual(source[row["start_char"]:row["end_char"]], row["src"])
                self.assertEqual(source[row["proof_start_char"]:row["end_char"]], row["proof"])
                self.assertEqual(source.encode()[row["start_byte"]:row["end_byte"]].decode(), row["src"])
                self.assertEqual(source.encode()[row["proof_start_byte"]:row["end_byte"]].decode(), row["proof"])
                if row.get("native_parser_complete"):
                    self.assertEqual(extraction.replace_proof(source, row, row["proof"]), source)

    def test_official_physlib_warmup_fields_match_exactly(self):
        snapshot = json.loads((ROOT / "data/arena_snapshot.json").read_text())
        warmups = extraction.read_jsonl(ROOT / "data/arena" / snapshot["arena_revision"] / "benchmark_data_warmup.jsonl")
        physlib = [r for r in warmups if r["source"] == "physlib"]
        self.assertEqual(len(physlib), 3)
        for warmup in physlib:
            matches = [r for r in self.rows if r["name"] == warmup["name"] and r["file_path"] == warmup["file_path"]]
            self.assertEqual(len(matches), 1, warmup["name"])
            for key in ["src", "statement", "proof_length", "num_lines", "header"]:
                self.assertEqual(matches[0][key], warmup[key], (warmup["name"], key))

    def test_private_nonrec_and_root_declarations_are_retained(self):
        self.assertTrue(any("private" in r.get("modifiers", []) for r in self.rows))
        self.assertEqual(sum("nonrec" in r.get("modifiers", []) for r in self.rows), 15)
        roots = [r for r in self.rows if r.get("local_name", "").startswith("_root_.")]
        self.assertEqual(len(roots), 36)
        self.assertTrue(all(r["name"] == r["local_name"].removeprefix("_root_.") for r in roots))


if __name__ == "__main__":
    unittest.main()
