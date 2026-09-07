# 056_lab_flag_summary — REDTEAM notes (Phase 4 PENDING)

## Mission
Produce the lab flag snapshot for this episode in `ops_reports` with three levels: a rollup of all `lab_results` flags, a per-`test_name` breakdown, and a per-species breakdown that joins `patients`. All counts must be exact and percentages rounded to one decimal.

## Why this is hard / unique
- Three-level aggregation (rollup, by-test, by-species) from a single source table.
- Species breakdown requires a correct `patients` join.
- `critical` is its own flag category, not a flavor of `abnormal`.
- Dual-path (SQL vs Python) verification on every count.
- Delete-then-rewrite idempotency per batch.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `lab_results` id=1 is the only row with `flag='critical'` (Serum chemistry panel, patient 4). Row evidence: `"flag": "critical"` appears once in the 42-row collection.
- `lab_results` id=7 references patient 27, whose `patients` row has `"status": "transferred"`. A species rollup that naively excludes transferred patients under-counts feline.
- The by-species and by-test row sets are dynamic; hardcoded row lists fail on reseed.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
