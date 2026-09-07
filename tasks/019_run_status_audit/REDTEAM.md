# 019_run_status_audit — REDTEAM notes

## Mission
Audit the boarding occupancy board against the reservation book. Set `audited` to the live batch_code on every run. Repair any run whose status or `current_patient_id` does not match the checked_in reservation (or the absence of one). Count reserved reservations that overlap occupied runs as `run_conflicts`. Do not modify reservations.

## Why this is hard / unique
- Requires reconciling three sources of truth: boarding_runs, boarding_reservations (status), and the episode-date interval.
- The `audited` field must be set on all 17 runs, not just the inconsistent ones.
- The run-conflict detection must find reserved-occupied overlaps without modifying the reservations.
- Dual-path verification: conflict count and run-status summary are checked via both Python and SQL.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- The snapshot is already internally consistent: runs 1-5 are occupied with current_patient_id 2, 4, 6, 8, 10 matching checked_in reservations 1-5; runs 6-17 are available.
- Reserved reservations 98 (run 4, patient 73) and 99 (run 3, patient 77) overlap the default episode date and share runs with occupied reservations 4 and 3. These are exactly 2 run_conflicts.
- Reserved reservation 8 (run 8) has check_out 2026-09-28, before the default episode, so it does not overlap and must not be counted.
- Reserved reservations 74, 128, 6, 65, 7, 17, 85 are active on the episode but on available runs (or shared with another reserved on the same available run), so they are not run_conflicts.
- A solution that uses the most recent reservation (reserved or checked_in) to set `current_patient_id` will set run 3 to patient 77 or run 4 to patient 73 and fail.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
