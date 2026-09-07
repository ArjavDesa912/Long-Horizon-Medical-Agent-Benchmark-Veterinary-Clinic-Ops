# 094_idempotent_daily_log_close — REDTEAM notes (Phase 4 PENDING)

## Mission
Close the boarding day by ensuring every checked_in reservation has a boarding_daily_log row for the episode date. New rows are existence-checked by the natural key (reservation_id, log_date) and the close summary is upserted in ops_reports.

## Why this is hard / unique
- 140 reservations; only the 5 checked_in ones need a log for the episode date.
- Episode date jitters ±3 days around 2026-09-30, so the target date is not the build date.
- Pre-existing seed daily logs for reservations 1-5 are on 2026-09-03 and 2026-09-04; a fixed-date or build-date solution will either skip the new rows or update the old ones.
- Idempotent insert: a second run must create zero new log rows and update the same report.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- 5 checked_in reservations (ids 1-5) with check_out before 2026-09-27; no seed log rows exist for the 2026-09-27..2026-10-03 episode window.
- Seed boarding_daily_log has 10 rows for reservations 1-5 on 2026-09-03 and 2026-09-04 (e.g., id 2 reservation 1 log_date 2026-09-04).
- 43 reserved and 92 checked_out reservations must be ignored.
- Blind insert without checking (reservation_id, log_date) duplicates on rerun.
- ops_reports must be upserted by batch_code.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
