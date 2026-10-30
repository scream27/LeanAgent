"""Fresh-process Lean measurement with explicit, frozen context templates."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import statistics
import subprocess
import time
import uuid

from .tokens import proof_tokens, validate_declaration

MARKERS = ("{{HARNESS_IMPORT}}", "{{HARNESS_COMMANDS}}", "{{DECLARATION}}")
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}

# Count exactly the target command, with the body elaborated synchronously.
# A fresh random log marker prevents accidental matching of unrelated messages.
WRAPPER = '''
open Lean Elab Command in
elab "#refactor_eval " tag:str target:str cmd:command : command =>
  show CommandElabM Unit from do
    let name := target.getString.toName
    if (← getEnv).contains name then
      throwError "evaluation target already exists before candidate"
    let start ← IO.getNumHeartbeats
    elabCommand cmd
    let finish ← IO.getNumHeartbeats
    let env ← getEnv
    unless env.contains name do
      throwError "candidate did not define evaluation target"
    let axioms ← Lean.collectAxioms name
    let report := Json.mkObj [
      ("target", toJson target.getString),
      ("raw", toJson (finish - start)),
      ("scaled", toJson ((finish - start) / 1000)),
      ("axioms", toJson (axioms.toList.map Name.toString))]
    logInfo m!"REFACTOR_EVAL {tag.getString} {report.compress}"
'''


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_text(path: Path) -> str:
    # No universal-newline translation: snapshot hashes describe actual bytes.
    return path.read_bytes().decode("utf-8")


def execute(command: list[str], cwd: Path, timeout: float, *, input_text=None, separate_stderr=False) -> dict:
    """Kill the process group on timeout, including Lake's child Lean process."""
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                               stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                               stderr=subprocess.PIPE if separate_stderr else subprocess.STDOUT,
                               start_new_session=True,
                               env={key: value for key, value in os.environ.items()
                                    if key in {"PATH", "HOME", "ELAN_HOME", "TMPDIR", "SYSTEMROOT", "WINDIR"}})
    timed_out = False
    try:
        output, stderr = process.communicate(input=input_text.encode() if input_text is not None else None,
                                             timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        output, stderr = process.communicate()
    except BaseException:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.communicate()
        raise
    return {"command": command, "returncode": process.returncode,
            "timed_out": timed_out, "seconds": round(time.monotonic() - started, 6),
            "output": output.decode("utf-8", errors="replace"),
            "stderr": (stderr or b"").decode("utf-8", errors="replace")}


def validate_template(template: str) -> None:
    for marker in MARKERS:
        if template.count(marker) != 1:
            raise ValueError(f"Template must contain exactly one {marker}")
        if not re.search(r"(?m)^" + re.escape(marker) + r"\s*$", template):
            raise ValueError(f"Template marker must occupy its own unindented line: {marker}")
    if not (template.index(MARKERS[0]) < template.index(MARKERS[1]) < template.index(MARKERS[2])):
        raise ValueError("Template markers must be ordered: import, commands, declaration")


def render(template: str, code: str, name: str, nonce: str | None) -> str:
    if nonce is None:
        values = ("", "", code)
    else:
        module = bool(re.search(r"(?m)^module\s*$", template))
        target = ("set_option Elab.async false in\n"
                  f"#refactor_eval {json.dumps(nonce)} {json.dumps(name, ensure_ascii=False)}\n{code}")
        values = (("public import Lean" if module else "import Lean"), WRAPPER, target)
    # Replace in one pass: never interpret marker-looking text in user proofs.
    replacements = dict(zip(MARKERS, values))
    return re.sub("|".join(map(re.escape, MARKERS)), lambda m: replacements[m[0]], template)


class LeanEvaluator:
    """Interface consumed by Session: fingerprint(env), evaluate(...)."""

    def fingerprint(self, environment: dict) -> dict:
        project = Path(environment["project"])
        toolchain = project / "lean-toolchain"
        if not toolchain.is_file() or read_text(toolchain).strip() != environment["toolchain"]:
            raise ValueError(f"Pinned lean-toolchain mismatch: {environment['id']}")
        command = environment["command"]
        version = execute([*command, "--version"], project, environment["timeout_seconds"])
        if version["returncode"] or version["timed_out"]:
            raise ValueError(f"Lean unavailable: {environment['id']}: {version['output'][-2000:]}")
        version_lines = [line for line in version["output"].splitlines() if line.startswith("Lean (version ")]
        if len(version_lines) != 1:
            raise ValueError("Could not identify the actual Lean compiler version")
        pin = re.search(r":v([0-9][^\s:]*)$", environment["toolchain"])
        if pin and not version_lines[0].startswith(f"Lean (version {pin[1]},"):
            raise ValueError("Actual Lean executable does not match the toolchain pin")
        prefix = execute([*command, "--print-prefix"], project, environment["timeout_seconds"])
        if prefix["returncode"] or prefix["timed_out"]:
            raise ValueError("Cannot resolve the actual Lean installation")
        compiler = Path(prefix["output"].strip()) / "bin" / ("lean.exe" if os.name == "nt" else "lean")
        compiler_hash = sha256(compiler.read_bytes())
        files = {}
        paths = {"lean-toolchain", "lake-manifest.json", "lakefile.lean", "lakefile.toml",
                 *environment.get("fingerprint_files", [])}
        for filename in sorted(paths):
            path = project / filename
            files[filename] = sha256(path.read_bytes()) if path.is_file() else None
        git = None
        # Do not accidentally use the enclosing application's Git repository.
        if (project / ".git").exists():
            head = execute(["git", "rev-parse", "HEAD"], project, 15)
            diff = execute(["git", "diff", "HEAD", "--", "."], project, 15)
            if head["returncode"] or diff["returncode"]:
                raise ValueError("Cannot fingerprint Git checkout")
            git = {"head": head["output"].strip(), "tracked_diff_sha256": sha256(diff["output"])}
        return {"project": str(project), "command": command, "version": version_lines[0],
                "compiler": str(compiler), "compiler_sha256": compiler_hash,
                "files": files, "git": git, "template_sha256": sha256(environment["template"])}

    def evaluate(self, code: str, config: dict, environments: list[dict],
                 output: Path, runs: int) -> dict:
        output.mkdir(parents=True, exist_ok=False)
        result = {"valid": False, "tokens": None, "environments": {}, "error": None}
        try:
            result["tokens"] = proof_tokens(code, config["statement"])
            validate_declaration(code, config["statement"])
        except ValueError as error:
            result["error"] = {"kind": "validation", "message": str(error)}
            return result
        for environment in environments:
            label = environment["id"]
            folder = output / label
            folder.mkdir()
            row = {"valid": False, "runs": [], "median_heartbeats": None, "error": None}
            result["environments"][label] = row
            try:
                self._evaluate_environment(code, config, environment, folder, row, runs)
            except (OSError, ValueError) as error:
                row["error"] = {"kind": "environment", "message": str(error)}
        result["valid"] = all(row["valid"] for row in result["environments"].values())
        if not result["valid"]:
            result["error"] = {"kind": "lean", "message": "One or more required environments failed"}
        return result

    def _evaluate_environment(self, code, config, environment, folder, row, runs):
        project = Path(environment["project"])
        # First compile the unchanged context with no injected imports/options.
        # This prevents extra imports in the measurement wrapper masking failures.
        jobs = [("check", None)] + [(f"measure-{i + 1}", uuid.uuid4().hex) for i in range(runs)]
        heartbeats = []
        for label, nonce in jobs:
            path = (folder / f"{label}.lean").resolve()
            source = render(environment["template"], code, config["name"], nonce)
            path.write_text(source, encoding="utf-8")
            invocation = execute([*environment["command"], "--root=" + str(folder.resolve()), str(path)],
                                 project, environment["timeout_seconds"])
            log = invocation.pop("output")
            log_path = folder / f"{label}.log"
            log_path.write_text(log, encoding="utf-8")
            record = {**invocation, "source": path.name, "source_sha256": sha256(source),
                      "log": log_path.name, "log_sha256": sha256(log)}
            row["runs"].append(record)
            if invocation["returncode"] or invocation["timed_out"]:
                row["error"] = {"kind": "timeout" if invocation["timed_out"] else "compile",
                                "message": log[-4000:]}
                return
            if nonce is None:
                continue
            matches = re.findall(r"REFACTOR_EVAL " + nonce + r" (\{[^\n]*\})", log)
            if len(matches) != 1:
                raise ValueError("Expected exactly one target heartbeat/axiom report")
            report = json.loads(matches[0])
            if report["target"] != config["name"]:
                raise ValueError("Measured target mismatch")
            if any(type(report[k]) is not int or report[k] < 0 for k in ("raw", "scaled")):
                raise ValueError("Invalid heartbeat counter")
            if report["scaled"] != report["raw"] // 1000:
                raise ValueError("Heartbeat unit mismatch")
            if not set(report["axioms"]) <= ALLOWED_AXIOMS:
                row["error"] = {"kind": "axioms", "message": str(report["axioms"])}
                return
            record["measurement"] = report
            heartbeats.append(report["scaled"])
        row.update(valid=True, median_heartbeats=statistics.median(heartbeats))
