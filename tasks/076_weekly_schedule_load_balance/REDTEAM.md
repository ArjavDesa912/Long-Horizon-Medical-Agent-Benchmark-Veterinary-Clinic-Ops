# 076_weekly_schedule_load_balance — REDTEAM notes

## Mission
Load-balance analysis for the coming week (episode date through episode date + 6 days inclusive). One ops_reports row per provider with role 'veterinarian': {report: 'weekly_load', batch_code, provider_id, provider_name, scheduled_hours: <sum over that vet's scheduled/confirmed appointments in the window of 30-minute slots / 2, as a number>, appointment_count, busiest_day: <the window date with their most appointments as YYYY-MM-DD; tie -> earliest; null if none>}.

## Why this is hard / unique
Slot-to-hours conversion, 7-day inclusive window, and per-row argmax with null case — compound conditions that punish shallow reads.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
