# 017_feeding_instruction_digest — REDTEAM notes

## Mission
The kitchen whiteboard needs today's feeding plan. Create one ops_reports row {report: 'feeding_digest', batch_code, on_episode_date: <episode date YYYY-MM-DD>, guests: <number of checked_in reservations>, raw_diets: <how many of those reservations' feeding_instructions contain the substring 'Raw' (case-sensitive)>, med_guests: <how many have medication_instructions other than 'None'>}. Exactly one row.

## Why this is hard / unique
Substring semantics (case-sensitive 'Raw') and 'None' literal exclusion trip agents that normalize text.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
