# 045_same_day_reschedule_block — REDTEAM notes

## Mission
Dr. Natarajan (provider id 3) called out sick. Move every 'scheduled' appointment of provider 3 that falls on or after the episode date to provider 4 (Dr. Okafor) and add field covering_for='3'. Confirmed appointments stay with provider 3 (clients were notified), and past appointments are history. Nothing else changes.

## Why this is hard / unique
Status-conditioned partial migration with a provenance field; moving confirmed rows is the tempting wrong answer.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
