# Lean Refactor Arena synthetic proof generator

This Python CLI mines real Strata theorems, prepares reference-conditioned prompts,
freezes five first responses per theorem, compiles whole files in disposable repository
copies, and reports all outcomes. It has no repair loop, resampling, RL, or cost tracking.

The checked-in run is in [`../synthetic-data/strata-50`](../synthetic-data/strata-50).
See its `report.md`, `summary.json`, `dataset.jsonl`, `theorems.jsonl`, `generation/`,
`references/`, `verification/`, and `charts/`. The source audit is [AUDIT.md](AUDIT.md).

## Environment

Python 3.10 or later, Git, [elan/Lake](https://github.com/leanprover/elan), and Matplotlib
are required. The tested Python is 3.12.14, on Windows. Run commands from the LeanAgent
repository root. `python` below means a real Python interpreter, not the Windows Store
alias. The generation/verification core needs no model SDK or API key.
Keep `.synthetic-cache/` out of version control (for example in your local
`.git/info/exclude`); it contains external checkouts, binaries and disposable copies.

```sh
python -m pip install matplotlib==3.10.8
git clone https://github.com/aurasoph/lean-refactor.git .synthetic-cache/aurasoph
git -C .synthetic-cache/aurasoph checkout 7f3a401470d04f70013d293db4253b088ec8a0ae
git clone https://github.com/strata-org/Strata.git .synthetic-cache/strata
git -C .synthetic-cache/strata checkout 451e5f047bafa010d178856db76c00029bfa4d7f
```

Strata pins `leanprover/lean4:v4.26.0`; Lake pins `plausible` to
`b949552f6ca8e223f424b3e3b33f74185bbf1179`. Build these modules from the Strata directory:

```sh
lake build Strata.DL.Util.StringGen Strata.DL.Util.Nodup Strata.DL.Util.List Strata.Languages.Core.FactoryWF Strata.DL.Lambda.LTyUnify Strata.DL.Lambda.Factory
```

The source checkout must be clean. Each compilation copies it, including its built
`.lake` dependencies, into a temporary directory and deletes that copy afterwards.
No hardlinks or shared writable dependency files are used. Compiled artifacts must
come from this pinned source and toolchain; do not import caches from another revision.
The delivered run used a preexisting local build cache and rebuilt these six module
targets in a clean archive of the pinned source before mining.

## Mine and validate ten references

Return to the LeanAgent root and choose a **new** output directory for a new run:

```sh
python -m synthetic mine --repo .synthetic-cache/strata --upstream .synthetic-cache/aurasoph --warmup .synthetic-cache/aurasoph/competition/benchmark_data_warmup.jsonl --output synthetic-data/new-run
```

`--warmup` is repeatable. The delivered run used both the local official warm-up
snapshot and the audited upstream copy; their Strata file exclusions agree:
`Strata/Languages/Core/StatementSemanticsProps.lean` and
`Strata/Transform/CallElimCorrect.lean`. All warm-up names are also excluded.
The exact hashes are in `exclusions.json`. Selection requires at least 31 nonempty,
noncomment proof lines and sorts by line count, path, then name. Each original full
file must compile, and the target's transitive axioms must pass. If fewer than ten
pass, the CLI reports a shortage rather than weakening filters.

The CLI saves exact statement/proof slices, full source snapshots, Git revision,
toolchain, proof offsets, hashes, inventory and complete reference logs. Statements
include their original whitespace before `:=`. Extraction conservatively supports
named `:=` theorems/lemmas; see the audit for scanner limitations.

## Generate and verify the pilot, then the remaining candidates

```sh
python -m synthetic prepare --dataset synthetic-data/new-run --phase pilot
```

For each generated `generation/<candidate-id>/prompt.txt`, provide the complete prompt
to the LLM and save its **first** response as a UTF-8 file. Every prompt contains the
exact statement, complete reference proof and full original source. Five controlled
refactoring objectives supply diversity. Never show compiler feedback during generation,
edit a response, strip fences, retry, or resample a duplicate. Import each response:

```sh
python -m synthetic submit --dataset synthetic-data/new-run --candidate-id ID --proof-file first-response.txt
```

`submit` refuses to overwrite a response, including a failing or malformed one.
The delivered run used the user-authorized shared Codex conversation and saved its
literal outputs in `pilot_responses.py` and `remaining_responses.py`. These envelopes
are data, loaded with `ast.literal_eval`, not code executed to mutate proofs:

```sh
python -m synthetic.import_responses --dataset synthetic-data/new-run --envelope synthetic-data/strata-50/pilot_responses.py
python -m synthetic verify --dataset synthetic-data/new-run --repo .synthetic-cache/strata --upstream .synthetic-cache/aurasoph --phase pilot
python -m synthetic review-pilot --dataset synthetic-data/new-run
python -m synthetic prepare --dataset synthetic-data/new-run --phase remaining
python -m synthetic.import_responses --dataset synthetic-data/new-run --envelope synthetic-data/strata-50/remaining_responses.py
python -m synthetic verify --dataset synthetic-data/new-run --repo .synthetic-cache/strata --upstream .synthetic-cache/aurasoph --phase remaining
python -m synthetic report --dataset synthetic-data/new-run
python -m synthetic validate --dataset synthetic-data/new-run --upstream .synthetic-cache/aurasoph
```

Importing the delivered responses **replays** generation; it does not perform new model
sampling. For a fresh experiment, supply fresh first responses instead. This shared-session
run does not meet statistical independence of separately seeded API requests; exact model
deployment, seeds, temperature, and API usage are unavailable. These limitations are
explicit in every request and the report. Prompt-controlled objectives are reproducible;
model outputs and wall-clock timings are not guaranteed identical across reruns.

The pilot gate requires all 15 attempts and no infrastructure failures, and stops an
all-failing pilot for inspection. Inspect `pilot-review.json` and raw diagnostics before
scaling. The remaining phase requires the pilot gate. Completed candidate IDs are not
regenerated or recompiled by resuming `verify`; use a fresh directory for an independent
verification replay. No failed candidate is ever repaired or discarded.

## Labels and metrics

- `compile_success`: actual exit-zero full-file Lean compilation, with the original
  imports/options/statement/suffix. It is independent of safety.
- `safety_passed`: conservative lexical rules plus transitive axiom checking for compiling
  candidates. For a noncompiling candidate it only describes lexical compliance;
  `axiom_check` is null. `propext`, `Classical.choice`, and `Quot.sound` are allowed.
- The axiom audit is a **second** invocation adding `#print axioms` immediately after
  the target. It is not used as the compilation-success measurement.
- `verification_time`: wall-clock seconds for the uninstrumented candidate compilation;
  excludes copy setup and the separate axiom audit.
- Proof tokens use pinned `local_score.tokenize_proof_body`, **not** LLM API tokens.
- `length_reduction_ratio = 1 - candidate/reference`; negative means longer.
  `candidate_reference_length_ratio` also records the direct length ratio.
- `duplicate_candidate`: exact proof-text match to an earlier attempt for the same theorem;
  duplicates remain in the denominator. Whitespace-equivalent terms are not collapsed.
- Error category is derived from actual diagnostics with deterministic precedence:
  resource exhaustion, syntax, unknown identifiers, type mismatch, unsolved goals,
  tactic failure, other. Full diagnostics remain in JSON and `.log` files.
- Heartbeats and unavailable generation usage are null, never invented zeroes.

Raw compiler JSON records the command, exit code, stdout, stderr, timeout and elapsed
seconds. Disposable absolute working paths may appear in raw logs and are expected to
differ on replay. Safety checks are not a hardened sandbox for arbitrary hostile Lean.
`reference_source_sha256` identifies the untouched Git source;
`verification_source_sha256` identifies the candidate's complete source file.
`source_sha256` inside verification results is also the candidate source checksum.
`python -m synthetic reclassify --dataset PATH` updates derived error labels from the
original diagnostics without rerunning Lean; changes are documented separately.

## Tests and licenses

```sh
python -m unittest synthetic.test_pipeline -v
```

Tests cover exact proof-only replacement, nested comment offsets, admission detection,
diagnostic categories, immutable first responses, null statistics and phase gating.
The delivered run also provides actual Lean verification for every reference/candidate.

Strata snapshots retain copyright headers and the MIT license in `licenses/STRATA-MIT.txt`.
The audited upstream Python repositories lack root license texts; helpers are imported
from pinned clones, not redistributed. See [AUDIT.md](AUDIT.md) before packaging them.
