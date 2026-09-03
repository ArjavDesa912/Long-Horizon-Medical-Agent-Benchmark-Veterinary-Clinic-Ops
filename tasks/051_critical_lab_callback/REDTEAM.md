# 051_critical_lab_callback — REDTEAM notes

## Mission
Critical lab values demand a documented callback. For every lab_results row with flag 'critical', push one communications row to that patient's owner: channel 'phone', direction 'outbound', subject 'URGENT lab result — <PatientName>', body '<test_name>: <result_summary>' (copied exactly), logged_by 'Dr. Alvarez', occurred_at on the episode date. Skip any critical result that already has a seeded communication whose subject starts with 'URGENT lab result'. Touch nothing else.

## Why this is hard / unique
Exact body copy-through (punctuation and units must survive) + already-handled exclusion.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
