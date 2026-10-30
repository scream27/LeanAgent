# Live conversation relay: 3 practice datasets

This experiment replaces only the common harness's model transport with a file-based live rendezvous (`external` backend). Responses are authored by the current conversation model **after** reading the actual request and preceding Lean feedback. They are not pre-generated fixtures. The normal request construction, proof parser, evaluator, candidate selection, budgets, final verification and record replay remain in the common harness.

## Dataset scope

- `arena_practice_benchmark.jsonl`: 15 rows
- `lean_refactor_eval_analysis_warmup_format.jsonl`: 10 rows
- `strata_local_practice_warmup_format.jsonl`: 10 rows
- 35 rows map to 29 unique declaration/source/context/version combinations. Duplicate rows share a run; they are not counted as independent evidence.
- `manifest.json` freezes hashes and row mappings. `progress.json` distinguishes pending, running, model-waiting, failed, and completed runs.

## Protocol

Each problem has at most 3 live model responses. A model request is persisted before delivery and bound by SHA256 to the reply. The reply contains a proof body in the existing `{"proof": "by ..."}` format. A response for another request is rejected. No API key or external model service is used. Harness API charge is zero; conversation token usage and subscription cost are not measured. The model's output token budget is not independently enforced like an API `max_tokens` limit; proof character limits are enforced.

The generation role uses only the supplied problem and feedback, as requested by the upstream system prompt. Environment setup and measurement are separate harness orchestration tasks. This conversation has historical exposure to related work, so this is not a blinded or independently replicated model evaluation.

## Evaluation

Prepared-environment evaluator from the prior experiment preserves full-file ordinary validation and checks target axiom dependencies against the original. The previously observed doc-comment/measurement-wrapper incompatibility is compensated in the measurement copy only. This is recorded adapter behavior, not a silent change to candidates.

Primary-version generation and extra-version compatibility verification must be reported separately. Pending environments are not counted as proof failures or passes. A failing original is classified before generating candidates. A final run must not be presented as an official leaderboard submission.

Raw runs are under `runs/live-practice-2026-10-28/<id>/raw`. Each step records its actual request, response, Lean diagnostics and resulting selection. Exchange files are outside sealed raw artifacts. `reason` in a delivered reply explains the model's chosen edit, not a Lean verdict. Replaying a completed record verifies bookkeeping, not Lean itself.

Do not restart an interrupted run into the same output directory or pre-fill future responses. Preserve failed runs and use a separate new run ID if restarting is needed.

## Current implementation

- `src/lean_agent/models.py`: external transport only.
- `src/lean_agent/harness.py`: accepts/validates external backend configuration.
- `tests/test_external_model.py`: real request/reply round-trip, feedback sequencing and replay, plus timeout accounting.
- `setup.py`, `run.py`, `reply.py`, `status.py`: experiment input creation and orchestration.

Scope and budgets are fixed before starting. No deliberate failures are injected into the practice proofs. Failed speculative refactorings, the model's repairs, unsuccessful retries, validation/measurement incompatibilities and environment failures will remain visible rather than being filtered from the report.

## Interrupted host sessions and durable continuation

The first waiting-process implementation was interrupted when a new conversation turn arrived. Pending replies had been written but no worker remained to consume them (`pgrep` found none). This is an orchestration/lifecycle failure, not a model proof failure. `resume.py` now runs only until the next missing model response and exits. A later invocation consumes the bound response and continues.

`resume.py` delegates parsing, feedback construction, metrics, ranking, budgets, summary and record replay to the same common-harness functions. It does not ask the model to choose a winner or calculate its own success. Completed baseline/evaluation result files are reused only after a matching full environment fingerprint; partial evaluation folders are preserved as `*-interrupted-N` before fresh re-execution. A copy of the resume adapter is frozen inside the raw record. The final common-harness record replay must still pass. `test_resume.py` verifies separate continuation calls preserve failure feedback, repairs and replay equivalence.

There is also a newly observed measurement-boundary bug: in practice problem 2, `set_option Elab.async false in` was parsed as a tactic belonging to the previous theorem. Ordinary original compilation succeeded, measurement failed. `run_v2.py` starts with the unambiguous `#refactor_eval` command and places `set_option ... in` inside the measured command. The original failing `raw` is retained; `raw-v2` is the corrected execution. These are distinct from invalid model candidates.

## Data exports

`analyze.py` writes selected proof bodies and primary-only score proxies to `selections.json`. `export_failures.py` writes observed rejected candidates, exact feedback and full logs to `repair-cases.jsonl`. No failures are injected. `report.py` renders the progress report. Token counts are the common harness source-token metric, not the earlier o200k_base BPE metric or model API usage.

## 2026-10-30 outcome and posthoc diagnostics

All 29 primary attempts are terminal: 16 final passes, 12 baseline rejections, and one final verification timeout. The 17 problems that reached generation consumed 51 conversation responses, with 13 rejected candidates. Three final passes retained the original proof (P9, P23, P25). These counts exclude duplicate dataset rows.

`retry_timeouts.py` separately rechecked three unchanged timeout outputs. All passed. `select_after_retries.py` uses the common ranking to select among the original, valid primary output, and valid retry results for P15/P19. `retry-selected-proofs.json` is an explicitly posthoc export; it does not overwrite the sealed primary run, and it makes no new model calls or proof edits.

`aggregate.json` states score denominators. Unverified rows do not receive invented zero scores. Primary-only proxies and local final scores with all requested versions measured are separate. These source-token scores are not directly comparable with an official leaderboard score.

Extra-version audits run the exact selected proof without generation, repair or reselection. Source checkouts and raw evidence survive sequential cleanup of generated toolchains and dependency caches.

## 사용자 요청에 따른 후속 실행 정책

앞으로 Lean 검증에는 wall-clock 시간제한을 두지 않는다(`lean.timeout_seconds: null`). 당시 180초는 대회 제한이 아니라 실험 운영 설정이었다. 후보의 비용은 기존 heartbeat 계측·점수로 비교하며 별도의 실행 시간 감점을 넣지 않는다. 기존 입력 snapshot, raw 결과, 과거 재시도 스크립트는 당시 프로토콜의 재현 자료로 보존한다. 새 입력 생성 및 호환성 검증 스크립트의 기본값은 무제한으로 변경했다. 과거 디렉터리를 재사용하거나 과거 점수를 새 정책의 결과로 바꾸지 않는다. 무제한 기준선 재실험은 아직 수행하지 않았다.
