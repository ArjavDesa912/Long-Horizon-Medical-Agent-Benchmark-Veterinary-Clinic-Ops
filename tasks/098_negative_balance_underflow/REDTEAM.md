# 098_negative_balance_underflow — REDTEAM notes

## Mission
Balances must never be negative (a credit is stored as a separate adjustment, not a negative balance). Find owners with balance < 0, move the negative amount into a new field credit_balance (positive number), set balance to 0, and tag them credit_fixed='<batch_code>'. Non-negative owners stay byte-identical.

## Why this is hard / unique
Sign-flip field migration with cents precision; the seed may contain zero negatives — in which case doing NOTHING is correct and the verifier accepts the pristine state ONLY for this collection... no: assert no row changed and no credit_fixed tags exist.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
