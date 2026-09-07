# 058_visit_note_completeness_score — REDTEAM notes (Phase 4 PENDING)

## Mission
Score visit-note completeness for this episode. A note is complete only if it has non-empty SOAP fields, a positive weight_kg, and a non-empty problems list. Write an `ops_reports` rollup with the sorted incomplete id list and a per-provider breakdown.

## Why this is hard / unique
- The completeness predicate now includes the `problems` list, which flips 207 additional rows from complete to incomplete.
- The per-provider breakdown requires a `providers` join for `provider_name`.
- The 208 incomplete ids must be a comma-joined sorted list.
- Dual-path verification (SQL JSONB array length vs Python list check).
- Delete-then-rewrite idempotency per batch.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `visit_records` id=371 has `plan=""`, but the bigger hazard is that the `problems` requirement makes 208 rows incomplete (e.g., id=2,3,4 all have `"problems": []`).
- `problems` is a list of objects; rows with `"problems": []` are incomplete.
- Only providers 1-4 appear in `visit_records`; the report must include only those providers with their `full_name` from `providers`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
