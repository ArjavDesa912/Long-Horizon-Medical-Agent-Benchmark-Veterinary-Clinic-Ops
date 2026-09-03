# 012_boarding_checkout_cleaning_cycle — REDTEAM notes

## Mission
Process departure for the checked-in boarding guest whose check_out date is earliest: set that reservation's status to 'checked_out', and move its run through the standard turnover — status 'cleaning' with current_patient_id cleared to null. Other guests stay put; touch no other rows.

## Why this is hard / unique
Turnover state machine (occupied→cleaning, not straight to available) matches real kennel practice; nulling the occupant is the step agents skip.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
