# Source audit (2026-10-16)

Inspected actual Python/Lean source from both repositories, not just READMEs.

- [delta-lab-ai/lean-refactor](https://github.com/delta-lab-ai/lean-refactor/tree/a2372caad69ab61a42a0e997106b87e00d9d7d65), commit `a2372caad69ab61a42a0e997106b87e00d9d7d65`.
- [aurasoph/lean-refactor](https://github.com/aurasoph/lean-refactor/tree/7f3a401470d04f70013d293db4253b088ec8a0ae), commit `7f3a401470d04f70013d293db4253b088ec8a0ae`.

## Extraction and measurement

| Implementation | Behavior and limitations | Decision |
|---|---|---|
| Delta `data_extraction/scripts/extract_repos.py`, `run_pipeline.py::_extract_module`, `preprocess_data.py::process_extracted_data` | Builds extraction projects, consumes declaration/premise JSONL, checks source inclusion, resolves dependency context and filters `sorry`. Requires extraction tooling and compatible Lean builds. `process_extracted_data` deletes an existing eval directory. | Keep as an alternative for large corpora; do not run its destructive output lifecycle for this small dataset. |
| Aurasoph `mining/find_problems.py::find_declarations`, `split_statement_body`, `extract_candidates` | Line-boundary scanning with a namespace/section stack, token and line limits, known-name filtering, optional LLM screening. Name filtering alone does not exclude whole warm-up files. The namespace stack omits `mutual`, so its `end` can pop a namespace incorrectly. Trailing comments can become part of a proof span. | **Reuse** scanner and assignment splitter through pinned imports. **Adapt** with nested-comment masking, exact offsets, corrected mutual scope tracking, file-wide warm-up exclusion, minimum 31 nonempty proof lines, full-file reference verification, and deterministic selection. No LLM screening. |
| Aurasoph `competition/local_score.py::tokenize_proof_body`, `remove_comments_po`, `lexer_po` | Arena-style lexical proof tokens, including operator joining; distinct from model tokens. Comment removal uses a nonnested regex and is imperfect for strings/nested comments. | **Reuse** at pinned revision for comparability; state limitations and method explicitly. Never call these counts API tokens. |

## Generation

| Implementation | Behavior and limitations | Decision |
|---|---|---|
| Delta `lean_refactor/agents/initial_optimizer_agent.py::_initial_optimizer` | Conditions on current proof, optional signature/dependencies; invokes an LLM, parses output and replaces the theorem statement. Retains optimization history for corrections. Framework imports LangChain/LangGraph, model integrations and other agents. | **Adapt** reference-conditioned prompt shape; replace orchestration with first-response file transport. Never normalize a changed statement into an apparently compliant candidate. |
| Delta `lean_refactor/agents/util/common.py::_extract_token_usage`, `TokenTracker`; `agents/util/debug.py::log_llm_prompt`, `log_llm_response` | Tracks model usage (missing usage defaults to zero upstream) and prints prompt/response interactions only when debug mode is enabled. Some surrounding functionality tracks costs and agent state, outside this task. | **Adapt** usage field semantics, keeping unavailable usage null; save complete task-specific prompts/responses without cost accounting. |
| Aurasoph `competition/arena.py::build_prompt`, `_openrouter_request`, `run_openrouter`, `run_codex`, `run_episode`, `best_checkpoint` | Supplies working-file context; runs tool-using episodes and checkpoint selection. Can retry, evaluate repeatedly, and restore best proofs. External model credentials or Codex CLI required. | **Replace** episode loop: exactly five frozen first responses, no compiler feedback during a phase's generation, no retry/repair/filtering. User chose this shared Codex session; no claim of independent seeded API sampling. |

## Verification and traces

| Implementation | Behavior and limitations | Decision |
|---|---|---|
| Delta `lean_refactor/util/verifier_slow.py::verify_lean4_file` | Runs `lake exe repl`, captures diagnostics/sorries/tactics and time; separates `pass` from `complete`. Requires a REPL executable, scheduler, NumPy/easydict; imports POSIX `resource`. `verifier_lean_client.py` and `util/interaction.py::LeanInteract` use `leanclient` and mutate/restore files. | **Adapt** distinction between compilation and admission safety; use full-file CLI compilation for this Windows environment, without REPL/server dependencies. |
| Aurasoph `competition/verify.py::build_project_file`, `run_one`, `hb_preamble` | Rebuilds source prefix plus candidate, drops the suffix, inserts Lean import/heartbeat elaborator, optionally disables limits, filters diagnostics to target and truncates errors to five. Success is based on heartbeat marker and filtered errors rather than process exit code. Timeout kills POSIX process groups. | **Replace** file assembly and acceptance: retain full suffix/imports/options, proof-only splice, disposable repository copies, exit-code success, complete stdout/stderr. Separate additional `#print axioms` audit allows only `propext`, `Classical.choice`, `Quot.sound`. Windows process-tree termination added. Heartbeats remain null because instrumentation would change this verification environment. |
| Aurasoph `training/harvest_traces.py::harvest`, `distill`, `distill_openrouter` | Copies raw rollouts and creates distilled events. Distilled fields truncate at 4,000 characters. `training/select_traces.py::best_per_problem` selects successful high-scoring examples. | **Adapt** raw/derived separation. Do not harvest unrelated conversation logs, reasoning, or choose only successful examples. Store complete generation response, prompt and compiler streams for every attempt. |

## Dependencies and licensing

Pipeline core: Python 3.10+, Git, Lake/Lean pinned by Strata; chart generation: Matplotlib. The upstream mining/scoring helpers use Python standard-library imports and the upstream benchmark module. Import them from an explicitly pinned local clone; no upstream Python source is vendored.

Delta's `pyproject.toml` advertises an Apache Software License classifier but the audited root contains no LICENSE file. Its full runtime pins Python 3.10.12 and includes LangChain providers, LangGraph, leanclient, Torch, vLLM, FAISS and ms_swift; these are unnecessary here. Aurasoph likewise has no root LICENSE in the audited tree. Public availability alone does not establish redistribution permission. Preserve attribution and avoid redistributing either repository's implementation files; clarify licensing with maintainers before packaging their code into a release. This audit is not a license grant.

Strata source headers explicitly say `Apache-2.0 OR MIT`. Redistributed reference/source snapshots retain headers, and the dataset includes Strata's MIT license. Warm-up exclusions are recorded as names/paths and hashes rather than redistributing the benchmark. Strata's pinned `plausible` dependency remains in the reproduction environment, not in this Git deliverable.

## Known scope limits

This is a conservative scanner, not a complete Lean parser. Unsupported lexical cases are skipped visibly; all accepted spans are checked against exact Git source and actual Lean compilation. Safety preflight is conservative and is not an OS sandbox for hostile Lean metaprograms. The generation prompt forbids metaprogramming and environment changes; compile-success candidates also receive a transitive axiom check. No repair agent, RL training, multi-agent optimization, or API price tracking is included.
