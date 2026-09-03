# 006_bordetella_boarding_gate — REDTEAM notes

## Mission
Clinic policy (standard boarding-kennel practice — verify online if needed): a dog may not check in for boarding unless its bordetella vaccination stays current through the end of the stay. For every boarding reservation with status 'reserved' whose patient is canine and whose latest bordetella due_date is on or before the reservation's check_out date, set the reservation's status to 'waitlisted_vax' and add a field hold_reason='bordetella lapse before checkout'. Leave every other reservation and field untouched. If a canine patient has no bordetella record at all, treat it as lapsed.

## Why this is hard / unique
Real kennel rule (vaccine must cover the whole stay, not just check-in day) + missing-record-implies-lapsed edge; date-window comparison against checkout, not today.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
