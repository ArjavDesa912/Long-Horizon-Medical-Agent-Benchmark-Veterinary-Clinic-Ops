# 072_fee_schedule_parity_check — REDTEAM notes

## Mission
Corporate wants to know if pricing is uniform. Compare the three locations' fee schedules item-by-item (match on code). Create one ops_reports row {report: 'fee_parity', batch_code, uniform: <true iff every code has identical price across all locations>, divergent_codes: <comma-joined sorted codes whose prices differ, or ''>, checked_codes: <count of distinct codes compared>}.

## Why this is hard / unique
Nested-array structural comparison across rows; agents compare row ids instead of item codes.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
