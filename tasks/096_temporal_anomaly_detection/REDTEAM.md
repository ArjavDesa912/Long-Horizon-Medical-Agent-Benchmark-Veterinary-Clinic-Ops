# 096_temporal_anomaly_detection — REDTEAM notes (Phase 4 PENDING)

## Mission
Read-only temporal-integrity sweep across the whole dataset. Identify six classes of temporal impossibility, count and list offending row ids, and write a single `ops_reports` row with `by_rule`, `row_refs`, and `clean`.

## Why this is hard / unique
- Cross-collection rules (lab vs visit, reminder due vs queued) require multi-hop joins, not just per-table filtering.
- The counts are large and noisy (274 time inversions, 344 early locked visits), so brute-force inspection is infeasible.
- Two of the rules (`estimate_expires_before_created` and a correctly handled `controlled_substance_log` null) are expected to be clean; a solution that omits them or reports a non-empty list fails.
- Every derived number is dual-path: a raw-row Python filter and an independent SQL query.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `appointment_time_inversion`: 274 rows. Row-level evidence: appointment id 7 `start_time` 12:30, `end_time` 12:00; id 9 start 15:30, end 15:00; id 10 start 11:30, end 11:00; etc.
- `vaccine_due_before_administered`: 10 rows. Evidence: vaccination id 100 patient 50 FVRCP `administered_date` 2026-08-19, `due_date` 2026-07-23; id 134 patient 67 bordetella administered 2026-07-15, due 2026-06-27; full list ids 100,134,217,256,294,301,482,487,581,591.
- `visit_locked_too_early`: 344 rows. Evidence: visit id 1 `visit_date` 2026-01-05, `locked_at` 2026-01-06 (1 day, < 30).
- `lab_result_before_visit`: 11 rows. Evidence: lab id 8 patient 275 `resulted_at` 2026-02-02, which is before the patient's latest `visit_date`; ids 8,12,13,14,23,25,26,28,32,38,39.
- `reminder_due_before_queued`: 1 row (id 1: `due_date` 2026-08-14, `queued_at` 2026-09-03). Reminder id 2 (`due_date` 2026-09-10) is after its `queued_at` (2026-09-04); reminder id 4 has no `due_date`.
- `estimate_expires_before_created`: 0 rows; all 100 billing_estimates have `expires_date` after `created_at`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
