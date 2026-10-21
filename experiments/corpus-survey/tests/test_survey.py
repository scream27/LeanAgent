"""Small tests for failure modes that would bias the lexical statistics."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("survey", Path(__file__).resolve().parents[1] / "scripts/survey.py")
survey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(survey)


class LexicalSurveyTests(unittest.TestCase):
    def test_nested_comments_do_not_count_and_keep_lines(self):
        text = "by\n /- simp /- exact -/\n grind -/\n simp only [foo] -- omega\n"
        self.assertEqual(survey.tactic_heads(text), [{"tactic": "simp", "line": 4, "form": "simp only"}])
        self.assertEqual(len(survey.mask_noncode(text)), len(text))

    def test_strings_and_quoted_characters_are_masked(self):
        text = '''def s := "by simp\\\"; omega"
def t := r##"by grind; exact"##
def c := 's'
example : True := by trivial
'''
        self.assertEqual(survey.counts(text), {"trivial": 1})

    def test_inline_combinators_and_apostrophes(self):
        text = "by induction h <;> (try simp_all); repeat' first | exact h' | (apply foo)"
        self.assertEqual(survey.counts(text), {"induction": 1, "simp_all": 1, "exact": 1, "apply": 1})

    def test_identifiers_and_attributes_are_not_heads(self):
        text = "@[simp] theorem my_simp : True := by\n  exact some_simp_lemma\n"
        self.assertEqual(survey.counts(text), {"exact": 1})

    def test_no_dynamic_goal_multiplier(self):
        self.assertEqual(survey.counts("by constructor <;> simp"), {"constructor": 1, "simp": 1})

    def test_both_goal_bullet_styles(self):
        self.assertEqual(survey.counts("by\n . apply List.Subset.trans\n · exact h"), {"apply": 1, "exact": 1})


if __name__ == "__main__":
    unittest.main()
