# 013_daily_log_completion — REDTEAM notes

## Mission
Kennel staff finished the evening round. For every reservation currently checked_in, make sure a boarding_daily_log row exists for the episode date with fed_am=true, fed_pm=true, medicated and walked reflecting that reservation's instructions (medicated=true only if medication_instructions is not 'None'; walked=true for all dogs — run_type 'kennel' or 'large_dog' — and false for cattery guests), notes='', and logged_by='Hank Willis'. If a row for that reservation and date already exists, update it to these values instead of creating a duplicate. Seeded log rows for other dates must remain untouched.

## Why this is hard / unique
Upsert (not blind insert) + instruction-conditional booleans through a reservation→run join; duplicate-creating agents fail the uniqueness check.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
