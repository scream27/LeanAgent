"""Control-flow and record-integrity tests. No model API or Lean installation needed."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from lean_agent import harness, models
from lean_agent.evaluator.lean import execute

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "examples/first-harness"


class FakeEvaluator:
    """Stable measurements let tests isolate harness behavior from Lean variance."""
    def __init__(self, environment_error=False, fail_final=False):
        self.calls = []
        self.environment_error = environment_error
        self.fail_final = fail_final

    def fingerprint(self, environment):
        return {"evaluator": "fake-for-unit-tests"}

    def evaluate(self, code, problem, environments, output, runs):
        output.mkdir(parents=True, exist_ok=False)
        self.calls.append(output)
        if ("False.elim" in code or self.environment_error and output.name == "evaluation"
                or self.fail_final and output.name == "final"):
            kind = "environment" if self.environment_error else "compile"
            return {"valid": False, "tokens": 2, "error": {"kind": "lean", "message": "failed"},
                    "environments": {"fixed": {"valid": False, "runs": [], "error": {
                        "kind": kind, "message": str(output / "fixed/check.lean") + ": failed"}}}}
        tokens = 2 if "rfl" in code else 6 if "simpa" in code else 14
        return {"valid": True, "tokens": tokens, "error": None,
                "environments": {"fixed": {"valid": True, "error": None,
                    "runs": [{"measurement": {"raw": tokens * 100}} for _ in range(runs)]}}}


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("PROJECT_CACHE_DIR"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(EXAMPLE, self.root / "fixtures")
        self.config = copy.deepcopy(harness.read(REPO / "configs/smoke.json"))
        for key in ("problem", "template", "project", "prompt"):
            self.config[key] = str((REPO / "configs" / self.config[key]).resolve())
        self.config["model"]["responses"] = str(self.root / "fixtures/responses.json")
        self.path = self.root / "config.json"
        self.output = self.root / "run"

    def save(self):
        self.path.write_text(json.dumps(self.config))

    def run_experiment(self, evaluator=None, output=None):
        self.save()
        return harness.run(self.path, output or self.output, evaluator=evaluator or FakeEvaluator())

    def test_invalid_candidate_never_wins_and_replay_uses_no_external_calls(self):
        evaluator = FakeEvaluator()
        result = self.run_experiment(evaluator)
        self.assertTrue(result["final_valid"])
        self.assertEqual(result["state"]["calls"], 3)
        self.assertIn("rfl", result["state"]["best"]["code"])
        self.assertEqual(len(evaluator.calls), 5)  # baseline + 3 attempts + final
        event = harness.read(self.output / "steps/001/event.json")
        self.assertFalse(event["state_after"]["latest"]["feedback"]["valid"])
        self.assertNotIn(str(self.output), event["state_after"]["latest"]["feedback"]["details"])
        with patch.object(models, "query", side_effect=AssertionError("model called")), \
                patch.object(harness.LeanEvaluator, "evaluate", side_effect=AssertionError("Lean called")):
            self.assertTrue(harness.replay(self.output)["record_replay_passed"])

    def test_unlimited_lean_timeout_survives_snapshot_and_replay(self):
        self.config["lean"]["timeout_seconds"] = None
        result = self.run_experiment()
        self.assertTrue(result["final_valid"])
        self.assertIsNone(harness.read(self.output / "input/config.json")["lean"]["timeout_seconds"])
        self.assertTrue(harness.replay(self.output)["record_replay_passed"])
        actual = execute([sys.executable, "-c", "print('finished')"], self.root, None)
        self.assertEqual(actual["returncode"], 0)
        self.assertFalse(actual["timed_out"])
        self.assertEqual(actual["output"].strip(), "finished")

    def test_timeout_validation_preserves_historical_positive_limits(self):
        for value in (None, 180):
            self.config["lean"]["timeout_seconds"] = value
            self.save()
            self.assertEqual(harness.load_config(self.path)[0]["lean"]["timeout_seconds"], value)
        for value in (0, -1, True, "unlimited"):
            self.config["lean"]["timeout_seconds"] = value
            self.save()
            with self.assertRaisesRegex(ValueError, "Lean timeout"):
                harness.load_config(self.path)

    def test_independent_runs_have_same_requests_without_shared_state(self):
        first = self.run_experiment()
        second_dir = self.root / "another-run"
        second = self.run_experiment(output=second_dir)
        self.assertEqual(first["state"], second["state"])
        for step in range(1, 4):
            relative = f"steps/{step:03}/request.json"
            self.assertEqual((self.output / relative).read_bytes(), (second_dir / relative).read_bytes())

    def test_artifact_tampering_is_detected(self):
        self.run_experiment()
        (self.output / "selected.lean").write_text("changed")
        with self.assertRaisesRegex(ValueError, "Artifact mismatch"):
            harness.replay(self.output)

    def test_archived_package_replays_from_another_working_directory(self):
        self.run_experiment()
        env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        result = subprocess.run(
            [sys.executable, "-B", str(self.output / "code/replay.py"), "replay", str(self.output)],
            cwd=self.root, env=env, capture_output=True, text=True, check=True,
        )
        self.assertTrue(json.loads(result.stdout)["record_replay_passed"])

    def test_execution_does_not_require_git_metadata(self):
        with patch.object(harness, "git_metadata", return_value=None):
            self.run_experiment()
        self.assertIsNone(harness.read(self.output / "manifest.json")["git"])
        self.assertTrue(harness.replay(self.output)["record_replay_passed"])

    def test_resealed_inconsistent_request_is_detected(self):
        self.run_experiment()
        request = self.output / "steps/002/request.json"
        data = harness.read(request)
        data["messages"][1]["content"] = "different context"
        request.write_text(harness.canonical(data))
        (self.output / "artifacts.json").unlink()
        harness.seal(self.output)
        with self.assertRaisesRegex(ValueError, "Request does not match"):
            harness.replay(self.output)

    def test_existing_run_is_never_overwritten(self):
        self.output.mkdir()
        (self.output / "keep").write_text("keep")
        with patch.object(models, "query") as query:
            with self.assertRaises(FileExistsError):
                self.run_experiment()
        query.assert_not_called()
        self.assertEqual((self.output / "keep").read_text(), "keep")

    def test_dangling_output_symlink_is_never_followed(self):
        self.output.symlink_to(self.root / "missing")
        with self.assertRaises(FileExistsError):
            self.run_experiment()
        self.assertFalse((self.root / "missing").exists())

    def test_resealed_false_success_summary_is_rejected(self):
        self.run_experiment()
        path = self.output / "summary.json"
        data = harness.read(path)
        data["stop_reason"] = "invented"
        path.write_text(harness.canonical(data))
        (self.output / "artifacts.json").unlink()
        harness.seal(self.output)
        with self.assertRaisesRegex(ValueError, "Final summary differs"):
            harness.replay(self.output)

    def test_malformed_response_still_consumes_a_call_and_records_cost(self):
        responses = ["not JSON", '{"proof":"by rfl"}', '{"proof":"by rfl"}']
        (self.root / "fixtures/responses.json").write_text(json.dumps(responses))
        result = self.run_experiment()
        self.assertEqual(result["state"]["calls"], 3)
        self.assertEqual(result["state"]["cost_usd"], "0")
        self.assertEqual(harness.read(self.output / "steps/001/event.json")["state_after"]["latest"]["feedback"]["status"], "response_rejected")
        self.assertTrue(harness.replay(self.output)["record_replay_passed"])

    def test_unknown_cost_stops_without_retry(self):
        raw = {"choices": [{"message": {"content": '{"proof":"by rfl"}'}}]}
        with patch.object(models, "query", return_value=raw) as query:
            result = self.run_experiment()
        self.assertEqual(query.call_count, 1)
        self.assertEqual(result["stop_reason"], "unknown_cost")
        self.assertEqual(result["status"], "stopped")
        self.assertTrue(result["state"]["unknown_cost"])
        self.assertTrue(harness.replay(self.output)["record_replay_passed"])

    def test_environment_failure_stops_without_charging_another_call(self):
        with patch.object(models, "query", wraps=models.query) as query:
            result = self.run_experiment(FakeEvaluator(environment_error=True))
        self.assertEqual(query.call_count, 1)
        self.assertEqual(result["stop_reason"], "environment_failed")
        self.assertTrue(harness.replay(self.output)["record_replay_passed"])

    def test_final_verification_failure_is_not_success(self):
        result = self.run_experiment(FakeEvaluator(fail_final=True))
        self.assertFalse(result["final_valid"])
        self.assertEqual(result["status"], "stopped")

    def test_context_limit_stops_before_model_call(self):
        self.config["limits"]["max_request_characters"] = 10
        with patch.object(models, "query") as query:
            result = self.run_experiment()
        query.assert_not_called()
        self.assertEqual(result["stop_reason"], "context_limit")
        self.assertEqual(result["state"]["calls"], 0)
        self.assertTrue(harness.replay(self.output)["record_replay_passed"])

    def test_baseline_failure_is_incomplete_not_a_new_trial(self):
        class InvalidBaseline(FakeEvaluator):
            def evaluate(self, *args):
                return {"valid": False, "environments": {}}
        with patch.object(models, "query") as query:
            with self.assertRaisesRegex(ValueError, "Original must verify"):
                self.run_experiment(InvalidBaseline())
        query.assert_not_called()
        with self.assertRaisesRegex(ValueError, "Incomplete run"):
            harness.replay(self.output)

    def test_model_cannot_change_statement_or_inject_declarations(self):
        from lean_agent.evaluator.tokens import validate_declaration
        problem = harness.read(EXAMPLE / "problem.json")
        for proof in ("by sorry", "by rfl\ntheorem injected : True := by trivial", "by native_decide"):
            raw = {"choices": [{"message": {"content": json.dumps({"proof": proof})}}]}
            code = harness.parse_proof(raw, problem, 4000)
            with self.assertRaises(ValueError):
                validate_declaration(code, problem["statement"])

    def test_duplicate_model_keys_rejected(self):
        raw = {"choices": [{"message": {"content": '{"proof":"by rfl","proof":"by sorry"}'}}]}
        with self.assertRaisesRegex(ValueError, "Duplicate model key"):
            harness.parse_proof(raw, harness.read(EXAMPLE / "problem.json"), 4000)

    def test_pinned_provider_request_and_credential_free_lean_child(self):
        payload = models.payload([], {"backend": "openrouter", "id": "test/model", "provider": "test-provider", "seed": 42})
        self.assertFalse(payload["provider"]["allow_fallbacks"])
        self.assertEqual(payload["provider"]["only"], ["test-provider"])
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-secret", "LEAN_PATH": "/not-frozen"}):
            import sys
            result = execute([sys.executable, "-c", "import os; print('OPENROUTER_API_KEY' in os.environ, 'LEAN_PATH' in os.environ)"], self.root, 5)
        self.assertEqual(result["output"].strip(), "False False")

    def test_no_live_request_with_placeholder_or_missing_key(self):
        self.config["model"] = {"backend": "openrouter", "id": "REPLACE", "provider": "REPLACE", "max_tokens": 100, "timeout_seconds": 5, "temperature": 0}
        with self.assertRaisesRegex(ValueError, "explicit model"):
            self.run_experiment()
        self.config["model"].update(id="test/model", provider="test-provider")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "OPENROUTER_API_KEY"):
                self.run_experiment()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
