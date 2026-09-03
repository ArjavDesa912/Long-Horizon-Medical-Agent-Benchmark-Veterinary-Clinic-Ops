# 001_overdue_vaccine_compliance_flag — REDTEAM notes

## Mission
The compliance officer needs an at-a-glance overdue marker. In the veterinary_clinic_system_vaccinations collection, add a field compliance_flag to every vaccination row: set it to 'overdue' when the row's due_date is strictly before the episode date recorded in veterinary_clinic_system_ops_meta.episode_date, 'due_soon' when the due_date falls within 7 days after the episode date (inclusive of the episode date itself), and 'current' otherwise. Do not modify any other field, and do not touch rows in any other collection.

## Why this is hard / unique
Rule-based conditional flagging derived from a live nonce date, not a fixed 'today'; no public benchmark uses a per-episode business-date anchor.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
