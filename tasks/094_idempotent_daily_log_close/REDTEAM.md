# 094_idempotent_daily_log_close — REDTEAM notes

## Mission
Close out the boarding day, re-runnable: for every checked_in reservation, ensure there is a boarding_daily_log row for the episode date. If missing, create it with fed_am/fed_pm/medicated/walked all false, notes 'auto-closed <batch_code>', logged_by 'system'. If a row for that reservation+date already exists, leave it completely unchanged. Running twice must create zero new rows the second time.

## Why this is hard / unique
Existence-checked insert (natural key: reservation+date); blind insert fails on duplicates.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
