# 018_boarding_overstay_flag — REDTEAM notes

## Mission
Flag every boarding overstay: reservation status 'checked_in' with check_out strictly before the episode date. For each, set status to 'overstay' and overstay_days, free the run, send an owner email, push an audit_log entry, and create an ops_reports summary with counts and breakdowns.

## Why this is hard / unique
- The overstay rule is strict (<) and status-based; the same reservations are also involved in other tasks, so the agent must not confuse them.
- The workflow writes to five collections and requires per-overstay communications and audit rows.
- All aggregates (count, total days, by run_type/location/species) are verified via dual raw-row + SQL paths.
- overstay_days is a whole-day date difference derived from the seed check_out and live episode date.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- At default episode 2026-09-30, the 5 checked_in reservations (ids 1-5) are all overstays, with overstay_days 21, 24, 24, 24, and 23 respectively.
- Reserved reservation 7 has check_out exactly 2026-09-30 (the default episode date); because the test is strict (<), it is NOT an overstay.
- Reserved reservation 8 has check_out 2026-09-28, before the episode, but is 'reserved' not 'checked_in', so it is a no-show, not an overstay.
- Runs 3 and 4 also have future reserved bookings (99 and 98); those reservations must remain untouched while the run is freed.
- The seed has 113 checked_out reservations and 260 pre-existing invoices; a solution that scans all reservations by date only over-flags.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
