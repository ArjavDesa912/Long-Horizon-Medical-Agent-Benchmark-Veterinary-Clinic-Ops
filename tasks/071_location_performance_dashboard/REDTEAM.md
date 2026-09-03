# 071_location_performance_dashboard — REDTEAM notes

## Mission
Recreate the org-admin 'All Locations' dashboard rollup. One ops_reports row per location: {report: 'location_rollup', batch_code, location_id, location_name, appointments_total, appointments_today: <appointment_date == episode date>, active_patients: <patients with status 'active'>, occupancy_pct: <round(100*occupied_runs/total_runs,1) from boarding_runs at that location>}.

## Why this is hard / unique
Four-metric join across three collections per location; mirrors the dashboard's org-admin toggle.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
