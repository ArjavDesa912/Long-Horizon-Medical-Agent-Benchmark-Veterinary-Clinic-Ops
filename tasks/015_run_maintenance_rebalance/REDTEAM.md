# 015_run_maintenance_rebalance — REDTEAM notes

## Mission
Run the end-of-month kennel capacity rebalance and deep-clean rotation. Eligible runs are derived from live reservation overlap on the episode date; per location the lowest-numbered eligible run and (at the most-occupied location) the highest-numbered distinct eligible run are set to 'maintenance'. Each selection is recorded in audit_log and summarized in an ops_reports row keyed by batch_code.

## Why this is hard / unique
- The correct set of runs changes with the episode date jitter and is not a fixed list.
- Eligibility requires a true interval overlap against all `reserved` and `checked_in` reservations, not just a count.
- The extra-run rule is anchored to the live most-occupied location, not a hardcoded large_dog preference.
- All aggregates (total, by-location) are verified via dual raw-row + SQL paths.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Runs K06, K07, C10, X15, X17 have overlapping reservations at the default episode date 2026-09-30 and must not be selected.
- Reservation 7 on run K07 has check_out exactly 2026-09-30, testing the inclusive boundary.
- Run_number prefixes K/C/X make global string sort produce wrong per-location minima.
- Location 3 has large_dog runs, but the most-occupied location is location 1, which has none, so a large_dog-preferring solution fails.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
