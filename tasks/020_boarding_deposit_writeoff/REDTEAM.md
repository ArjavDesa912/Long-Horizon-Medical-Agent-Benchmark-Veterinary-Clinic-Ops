# 020_boarding_deposit_writeoff — REDTEAM notes

## Mission
No-show policy time. A 'reserved' reservation whose check_in date has passed (strictly before the episode date) without the guest arriving is a no-show. For each one: set the reservation status to 'cancelled' and add cancellation_reason 'no_show'. Then charge the standard no-show fee the clinic applies — one night's boarding at that location's BOARD-NIGHT fee-schedule rate — by INCREASING the owner's balance by exactly that amount (verify typical kennel no-show fee practice online if unsure; one night is the common standard). Owners with multiple no-show reservations are charged once per reservation. Touch nothing else.

## Why this is hard / unique
Balance mutation must be additive to a live value (not absolute) and aggregated per owner; fee rate comes from a fee-schedule join, not the instruction.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
