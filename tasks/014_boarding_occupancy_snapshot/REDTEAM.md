# 014_boarding_occupancy_snapshot — REDTEAM notes

## Mission
Record the occupancy snapshot the morning huddle uses. Create veterinary_clinic_system_ops_reports with one row per location: {report: 'boarding_occupancy', batch_code: <episode batch code>, location_id, total_runs, occupied_runs, occupancy_pct: <round(100*occupied/total, 1)>}. Exactly 3 rows.

## Why this is hard / unique
Simple aggregation but exact-count + live-nonce fields defeat hardcoding; baseline of the report family.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
