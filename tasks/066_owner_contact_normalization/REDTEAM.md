# 066_owner_contact_normalization — REDTEAM notes

## Mission
Normalize owner contact data for the SMS gateway: rewrite every owner's phone to E.164-ish digits-only form '+1' followed by the 10 digits (strip punctuation; all seeded numbers are US 10-digit like '(828) 555-0101'), and lowercase every owner's email. Add field contact_normalized='<batch_code>' to every row you change. Rows already compliant keep their values but still get the tag. Do not change names, addresses, or balances.

## Why this is hard / unique
Deterministic string normalization across a whole collection; the digits-only transform must preserve the area code correctly.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
