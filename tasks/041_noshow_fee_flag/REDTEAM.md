# 041_noshow_fee_flag — REDTEAM notes

## Mission
Front-desk cleanup: every appointment with status 'no_show' must carry a follow-up marker. Add field follow_up='call_owner' to each no_show appointment and leave every other appointment byte-identical.

## Why this is hard / unique
Baseline surgical update; the byte-identity guard on untouched rows defeats bulk-rewrite hacks.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
