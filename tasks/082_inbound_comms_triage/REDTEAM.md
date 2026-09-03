# 082_inbound_comms_triage — REDTEAM notes

## Mission
Triage the comms inbox: add field triage='needs_reply' to every communications row with direction 'inbound', and triage='fyi' to every 'outbound' row. No other changes.

## Why this is hard / unique
Whole-collection two-class tagging with byte-identity on untouched fields.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
