# 099_full_state_reconciliation — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the full boarding-ward state reconciliation for the episode date. Reconcile the kennel occupancy board (`boarding_runs`), the checked-in reservations (`boarding_reservations`), the daily care log (`boarding_daily_log`), and the patient master records (`patients`) into a single `ops_reports` row. The row must report counts, a bidirectional consistency flag, run mismatch ids, log coverage, and patient location/active-status mismatches.

## Why this is hard / unique
- **Four-way reconciliation**: the report joins four different collections with real referential dependencies; the counts and mismatch lists must all agree.
- **Bidirectional join verification**: an occupied run must have a matching checked-in reservation and vice versa, catching one-sided updates.
- **Decoy rows and subtle mismatches**: the data includes available runs, reserved/checked-out reservations, and a transferred patient, but only the five checked-in boarders are in scope.
- **Episode-date log window**: `boarding_daily_log` coverage must be judged against the live episode date, and existing non-episode logs must remain untouched.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Only `boarding_reservations` id=1-5 are `status='checked_in'`; id=6-140 are `reserved` or `checked_out`.
- `boarding_runs` id=1-5 are `occupied` with `current_patient_id` 2,4,6,8,10; id=6-17 are `available` with null `current_patient_id`.
- Checked-in reservation id=5 and run id=5 have `location_id='1'`, but patient id=10 has `location_id='2'`.
- Patient id=27 has `status='transferred'` and is not boarding.
- `boarding_daily_log` rows 1-10 cover reservations 1-5 on `2026-09-03` and `2026-09-04`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
