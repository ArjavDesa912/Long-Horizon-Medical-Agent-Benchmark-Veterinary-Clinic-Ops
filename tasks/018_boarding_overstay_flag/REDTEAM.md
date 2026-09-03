# 018_boarding_overstay_flag — REDTEAM notes

## Mission
Guests still checked in past their scheduled check_out are overstays. For every reservation with status 'checked_in' whose check_out is strictly before the episode date, set status to 'overstay' and add overstay_days = <whole days between check_out and the episode date>. Reservations checking out exactly on the episode date are NOT overstays. Do not touch runs or other reservations.

## Why this is hard / unique
Strict-vs-inclusive boundary (checkout on the day itself is not an overstay) — the classic off-by-one.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
