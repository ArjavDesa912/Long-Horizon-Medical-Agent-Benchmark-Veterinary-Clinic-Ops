# 092_idempotent_occupancy_sync — REDTEAM notes (Phase 4 PENDING)

## Mission
Reconcile the 17 boarding_runs against the reservation book as of the jittered episode date. A run is occupied only when a checked_in reservation covers the episode date (check_in <= ep < check_out). Only changed runs carry the synced watermark, and the operation is documented by a single audit_log row.

## Why this is hard / unique
- Date-windowed reconciliation: the agent must filter checked_in reservations by the episode date, not just by status.
- The seed snapshot already has runs 1-5 marked occupied, but none of the checked_in reservations cover the late-September episode date, so the expected final state is all runs available.
- synced must be stamped only on runs whose state actually changes; over-eager re-tagging fails.
- Single audit log entry per sync operation, with idempotent suppression on re-run.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- checked_in reservations ids 1-5 have check_out dates 2026-09-06/2026-09-07, all before episode dates 2026-09-27..2026-10-03, so the active set is empty.
- 43 reserved and 92 checked_out reservations with overlapping run_ids; status and date range must both be checked.
- boarding_runs 1-5 are occupied with current_patient_id 2/4/6/8/10 in the snapshot; runs 6-17 are available.
- A solution that sets synced on all 17 runs fails because runs 6-17 are unchanged.
- A solution that appends an audit row every run fails duplicate audit check.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
