# 020_boarding_deposit_writeoff — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the month-end boarding no-show forfeiture pass. Cancel reserved reservations whose check_in has passed, charge the location's BOARD-NIGHT fee to the owner, notify each affected owner, append an audit entry per no-show reservation, and push a summary ops_report. The pass must be idempotent and leave all non-target reservations untouched.

## Why this is hard / unique
- Multi-collection transaction spanning boarding_reservations, owners, fee_schedules, patients, communications, audit_log, and ops_reports.
- Fee is derived from a fee-schedule join, not a constant.
- Owner-balance mutations are additive and aggregated per owner.
- Target set shifts with the episode-date jitter (±3 days), so hardcoded counts and ids fail.
- Red-herring future reserved rows and non-reserved (checked_in/checked_out) rows are planted in the same collection.
- Dual-path (Python filter + SQL count) verification on the no-show aggregate and total fees.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Future reserved decoys: the 140-row boarding_reservations snapshot has 22 reserved rows, but only 10 of them have check_in before the default episode 2026-09-30. Concrete future decoys that must remain untouched: id 18 (patient 35, check_in 2026-10-13), id 20 (patient 200, check_in 2026-10-27), id 51 (patient 129, check_in 2026-10-24). At 2026-09-27 the target count drops to 7 (ids 6,7,8,17,65,85,98), so any hardcoded target list is wrong.
- Non-reserved decoys: ids 1-5 are checked_in and ids 9-15/16/50/100/140 are checked_out; these must survive byte-identical.
- Fee-schedule join: all three fee_schedules contain a BOARD-NIGHT item priced at $38, but the solution must read it from the location's fee schedule, not hardcode 38.
- Owner balance is an existing field; the verifier re-derives the expected final balance per owner as seed balance plus the per-owner fee sum.
- Multi-owner collision: none in this seed (each no-show is a different owner), but the code must aggregate by owner in case the target set ever overlaps.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
