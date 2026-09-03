# 038_controlled_dea_schedule_backfill — REDTEAM notes

## Mission
Regulatory backfill: every medication with is_controlled_substance=true must carry the correct DEA schedule in dea_schedule. Any controlled row missing dea_schedule must be fixed using the schedule that the OTHER rows for the same drug_name already use (the clinic's existing classifications are authoritative). If no other row for that drug exists, look up the drug's current DEA schedule online. Non-controlled rows must not gain a dea_schedule. Add field schedule_fixed='<batch_code>' to each row you change.

## Why this is hard / unique
Self-referential repair (derive the fix from sibling rows) with a web-knowledge fallback branch; tagging only changed rows.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
