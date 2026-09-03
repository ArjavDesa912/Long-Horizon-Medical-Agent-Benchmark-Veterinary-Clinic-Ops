# 074_cross_location_patient_moves — REDTEAM notes

## Mission
How much inter-location traffic is there? One ops_reports row {report: 'transfer_matrix', batch_code, matrix: <JSON object 'from->to' -> count of location_transfers rows with that from/to pair (all statuses)>, pending_total, completed_total, most_active_lane: <the 'from->to' key with the most transfers; tie -> alphabetically first>}.

## Why this is hard / unique
Composite-key counting serialized into a JSON object with deterministic tiebreak.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
