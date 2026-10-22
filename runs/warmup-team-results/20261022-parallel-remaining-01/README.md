# Remaining problem verification — first pass

P08 and P09 passed baseline and candidate checking in Lean v4.31.0 and v4.32.0, each with three measurements. P08 has one imported candidate; P09 has two identical imported candidate bodies with separate author provenance. Required v4.33.0-rc2 (P08/P09) and v4.30.0 (P08) environments remain unavailable, so these are partial version checks, not fully verified entries.

P05 plain compilation passed, but measurement was blocked by the runner treating a preceding module comment as a declaration doc comment. This run's P05 result is superseded by `../20261022-parallel-remaining-02/`. No candidate was altered.

P10 and P13–P15 remain environment-blocked. See `environment-audit.json` for exact missing dependencies and pins. Different installed versions were not substituted.

`environments.local.json` records local compiler and library paths. `preparation-report.json` records supplement module hashes and matching dependency pins. The isolated file-level overlays resolve Lean's first-prefix search behavior across partial library roots. Existing source and build directories were read-only. No model API was used.

`verify.py.snapshot` is the exact runner whose SHA256 appears in `summary.json`; `prepare_remaining.py.snapshot` captures the dependency-preparation utility. Logs and original evaluator JSON are retained below each problem. The runner uses evaluator revision c18ec56682462847e2f4d8b6d60aa79ec071a10b.
