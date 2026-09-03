# 099_full_state_reconciliation — REDTEAM notes

## Mission
Prove the boarding books balance three ways, in one row. Create one ops_reports row {report: 'boarding_recon', batch_code, occupied_runs: <runs status 'occupied'>, checked_in_reservations: <reservations status 'checked_in'>, runs_with_occupant_field: <runs with non-null current_patient_id>, consistent: <true iff occupied_runs == checked_in_reservations AND every occupied run's current_patient_id equals its checked_in reservation's patient>, mismatch_run_ids: <comma-joined ascending ids of runs failing the equality, or ''>}.

## Why this is hard / unique
Three-way consistency proof with a mismatch listing; agents assert counts and skip the per-run occupant equality.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
