# 040_controlled_refill_freeze — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the controlled-substance refill freeze and compliance summary. For every active controlled medication with refills remaining and prescribed more than 90 days before the episode date, freeze refills, tag with the batch code, log an audit row, and produce a per-drug `ops_reports` summary (one row per controlled drug name plus an ALL rollup).

## Why this is hard / unique
- The target rule is implicit in DEA policy (age + controlled + active + refills > 0) and must be derived from live data, not stated as a list of IDs.
- Multiple red-herring classes sit near the boundary: null `dea_schedule` on a controlled row, refills already at 0, recent prescriptions with refills, and non-controlled medications.
- The episode date jitters, so the 90-day cutoff is live and not hardcoded.
- Every aggregate in `ops_reports` is verified by two independent derivations (Python filter and SQL `GROUP BY`) and must agree.
- Idempotency: rerun must not duplicate audit rows or summary rows.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `medications` id=2 (Alprazolam, is_controlled_substance=true, dea_schedule=null, prescribed_at 2026-05-07, refills=1) proves the correct filter is `is_controlled_substance`, not `dea_schedule`.
- `medications` id=18, 50, 58 (controlled, active, refills=0, prescribed_at before the 90-day cutoff) are decoys that satisfy age and controlled flags but must not be frozen.
- `medications` id=46, 62, 166, 174 (controlled, active, refills=1, prescribed_at in July/August 2026) are decoys that have refills but are too recent.
- Non-controlled active medications (e.g., Carprofen, Gabapentin, ~150 rows) must remain untouched.
- Inactive medications (28 rows) must remain untouched.
- The cutoff is right at the edge of the July-dated controlled rows (id=38 Tramadol 2026-07-05, refills=0), so a hardcoded or off-by-one cutoff will misclassify.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
