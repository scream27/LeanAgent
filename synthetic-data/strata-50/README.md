# Strata 50-candidate run

Read [report.md](report.md) for measured outcomes and [summary.json](summary.json)
for machine-readable statistics. Reproduction and CLI documentation are in
[../../synthetic/README.md](../../synthetic/README.md); the upstream source audit
is [../../synthetic/AUDIT.md](../../synthetic/AUDIT.md).

- `dataset.jsonl`: all 50 first-attempt candidates, including the 15-candidate pilot.
- `theorems.jsonl`: ten compiled references with exact statements, proofs and provenance.
- `sources/`: complete original Strata files; `licenses/`: source license.
- `generation/`: complete prompts, first responses, hashes and explicit sampling limitations.
- `references/`, `verification/`: full source files, compiler streams, commands, timings and axiom audits.
- `pilot-review.json`: pilot infrastructure gate before remaining generation.
- `integrity.json`: final artifact consistency checks.
- `charts/`: four exported PNG charts.
- `pilot_responses.py`, `remaining_responses.py`: literal model-response envelopes for replay.

Generation used the shared Codex session at the user's request. The five attempts
per theorem use different refactoring objectives, but are not statistically independent
API samples. No API seed, temperature, exact deployment identifier, usage tokens,
or heartbeat measurements are available. Null means unavailable, not zero.

Do not train on only the successful rows without recording that selection: failed
and duplicate first responses are intentional parts of this dataset. No candidate
was repaired or regenerated after compiler feedback.
