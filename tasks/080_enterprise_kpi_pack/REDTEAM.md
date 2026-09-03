# 080_enterprise_kpi_pack — REDTEAM notes

## Mission
The Monday leadership pack, all KPIs in one row. Create one ops_reports row {report: 'kpi_pack', batch_code, on_episode_date: '<YYYY-MM-DD>', appointments_today, boarding_occupancy_pct: <100*occupied/total runs, round 1>, vaccinations_overdue: <vaccinations with due_date strictly before episode date>, outstanding_balance_total: <sum over owners of balance, dollars>, open_invoices: <invoices status 'sent' or 'overdue'>, critical_labs_open: <lab_results flag 'critical'>}.

## Why this is hard / unique
Six-source KPI fan-in matching the dashboard's KPI row definitions; each KPI has its own subtlety (strict-before, status set, float sum).

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
