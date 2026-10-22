# Experiment A: AST Local Proof Minimizer

2026-10-21 · 남성우 · warm-up development experiment.

## Question and comparison

Does bounded local minimization improve the final combined score of proofs already
selected by the existing pipeline, without another model call?

The control is the frozen `control_selected.json` from the 2026-10-15 sweep.
This is a post-processing comparison, **not** a fresh model generation comparison
or a rerun of all 45 historical prompt outputs. The original proof is an independent
fallback. P8 remains original-only, as previously requested by the user.

`warmup.jsonl` is the development set. The three proposed practice/test JSONL files
were not used to choose tactics, thresholds or outcomes in this experiment.

## Implementation

- `Profile.lean`: parse-time Lean `Syntax` traversal, original UTF-8 byte positions.
- `minimize.py`: supported full-line tactic nodes and indented tactic sequences;
  deletion, `simp?`, `exact?`, `aesop?`, `assumption`, `rfl` proposals. Strata skips
  `aesop?`. Two largest sequences and two largest standalone tactics per round,
  at most 24 proposals / 3 rounds per problem. Stable source-size / offset ordering.
- Query suggestions are extracted from JSON diagnostics at the edited source line.
  This initial implementation supports conservative single-line suggestions only.
  The query proof itself is never eligible for final selection. Extracted scripts
  are independently checked and measured. Suggestions from unsuccessful queries
  may still be tested, but only the explicit full replay can establish validity.
- `verifier.py`: adapted snapshot of the existing `run_sweep.py` verifier, with
  structured diagnostic preservation and source-token measurement. Runs full-file
  validation, target axiom check, then separate synchronous declaration HB measurement.
- The fixed statement and surrounding source are preserved by body replacement.
  Generated edits are constrained AST splices; the text blacklist is not claimed
  to be a sandbox for arbitrary adversarial Lean code.
- Every valid explicit proposal is retained, including worse proposals. All are
  checked unchanged on all listed versions before final selection. Search on the
  primary version is greedy; a cross-version failure can therefore make its search
  path suboptimal, but cannot silently turn into an eligible unverified submission.
- A non-improving valid control is replaced by independently verified original for
  the comparison. Ties retain the current control/original. All selected proposals
  must preserve the per-version baseline axiom allowance.

This adds an optimizer after the old selector. It does not implement B, C, semantic
dependency analysis, model execution or a learned adaptive scheduler. Failed local
proposals are search evidence; this run does not escalate each proposal to an LLM.

## Metrics

`score = [100*(1-L/L0) + 100*(1-H/H0) + 100*passed_versions/total_versions] / 3`.

- Tokens: the team's `proof_tokens.py` reconstruction, copied from upstream main.
  All 15 reference lengths agree with the warm-up `proof_length` field. It is not
  the earlier sweep's o200k_base count. Old displayed scores are not reused.
- HB: declaration `IO.getNumHeartbeats` delta / 1000 with `Elab.async=false`, freshly
  measured for original and control in the primary (first listed) environment.
- Robustness: identical body checked on every listed version. Missing, timeout,
  and environment error mean incomplete scoring, not a fabricated failure rate.
- These are local final combined scores, not official Arena worker submissions.
- Runtime / local Lean invocation count are operating costs, not the candidate's HB.
- No new model API calls. This does not claim that development or historical model
  candidate generation had zero total cost.

## Reproduce

Python standard library and an installed elan/Lean/Lake launcher are required. Setup needs
network access. Existing historical clones are reused when available; otherwise the runner
clones the public source URL from the frozen benchmark. `LEAN_ARENA_WORKSPACE` can select
a workspace containing historical `refactor_arena` environments. The default scans parent
directories and falls back to a scratch-only setup. Lean 4.26 uses the default elan home. Run commands from the repository's workspace root:

```sh
python3 -m unittest discover -s LeanAgent/docs/research/verifier-guided-agent/experiments/local-minimizer-2026-10-21 -p 'test_*.py' -v
python3 LeanAgent/docs/research/verifier-guided-agent/experiments/local-minimizer-2026-10-21/prepare.py
python3 LeanAgent/docs/research/verifier-guided-agent/experiments/local-minimizer-2026-10-21/report.py
```

`prepare.py` resumes completed per-version results; absent results run from scratch.
For an independent rerun, copy the implementation and frozen inputs to a new run
directory, with the same workspace-root arrangement. Do not overwrite old evidence.
The experiment-owned `scratch/` caches/toolchains/checkouts are removed after a
successful environment job under the user's explicit authorization. Existing user
projects, historical experiment environments and previous logs are not deleted.

## Evidence and limitations

`freeze.json` records code/input hashes before the main run. `runs/<id>/<version>/`
holds source snapshots, raw JSON diagnostics, normalized text, axiom checks,
measurement commands, AST profiles and candidate outcomes. `pool/` freezes explicit
candidate bodies for cross-version validation. `setup_logs/` records environment
preparation. `results.json`, `results.csv`, `summary.json` and `presentation.html`
are generated from completed evidence; incomplete rows are explicitly marked.

Two preliminary P1 pilots are retained in `pilot/`, excluded from final accounting.
They exposed missing position metadata in ordinary `Try this` text and over-selection
of large sequence nodes. Before the main run, JSON diagnostics, a supported-node
filter and sequence/atomic-site allocation were implemented. A unit-test fixture
was corrected to exceed the deliberate eight-byte minimum site length.

Only syntax structure is profiled. No dependency-depth or mathematical-readability
improvement is asserted. One run per condition; tiny HB differences need replication.
The support whitelist excludes inline branches and unsupported custom syntax.
Three rounds and 24 proposals are ceilings, not guaranteed work quotas: no-progress
rounds terminate. A query plus explicit replay can cause multiple Lean invocations.
Final non-regression is ensured by selection/fallback, not by universal proposal quality.

Proof token implementation provenance:
`Pseudo-Lab/LeanAgent/docs/research/refactoring/warmup/박채원/evidence/local-v4.26/tools/proof_tokens.py`.
Verifier provenance: `refactor_arena/prompt_sweep_2026_10_15/run_sweep.py`.
Proof excerpts retain their upstream source licensing; generated evidence includes upstream source snapshots; the original project
checkouts are not modified by the verifier.


### Profiler compatibility revision

The first PhysLib profile exposed two Lean module-system requirements: helper code
used at compile time must be marked `meta`, and a documentation comment cannot
attach to the profiling wrapper. The profiling copy now places helpers after imports
and converts a trailing theorem documentation comment to an ordinary comment.
The actual verification and measurement copies are unaffected. The failed profile
is retained in `pilot/p04-profiler-compatibility/`. The previous freeze is retained
as `freeze-v1.json`; normalized P1 AST node equality is recorded under `compatibility/`.
Search operators, site ranking, and budgets were not changed by this revision.


Official scoring wording was rechecked on 2026-10-22 in the public
[Arena app](https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/blob/main/app.py),
`_scoring_html`; see `scoring-source.json`. Local remeasurement remains distinct
from official worker scoring. Historical raw observation records retain the legacy
`measurement_kind` string mentioning `o200k_base`; in this experiment the executable
token counter is `proof_tokens.py`, as verified by `freeze.json`, not that legacy label.
The original source license notices are preserved in `licenses/`.

### Secondary-version validation correction

P10 on Lean 4.28 passed the full original proof, but unnecessary secondary HB
instrumentation failed in an `omit ... in` / documentation-comment context.
Only the first version's HB enters the score. Secondary runs now validate the
full file and axiom dependency without requesting unused heartbeat measurements.
The failed run is retained in `compatibility/p10-secondary-measurement-failure/`,
and the previous code freeze in `freeze-v2.json`. Search, ranking, primary
measurement, and score calculation are unchanged. `test_secondary.py` prevents
reintroducing a requirement for secondary HB. Earlier secondary HB observations
remain in the evidence but do not contribute to scoring.
