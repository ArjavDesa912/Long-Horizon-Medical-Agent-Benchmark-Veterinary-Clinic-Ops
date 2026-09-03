# 044_provider_utilization_report — REDTEAM notes

## Mission
How busy is each doctor? One ops_reports row per provider with role 'veterinarian': {report: 'provider_utilization', batch_code, provider_id, provider_name, total_appointments, completed, no_shows, upcoming: <appointments with appointment_date on or after the episode date and status in ('scheduled','confirmed','checked_in')>}. Any order; only veterinarians.

## Why this is hard / unique
Role-filtered group-by with a status-set + date-window compound condition for 'upcoming'.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
