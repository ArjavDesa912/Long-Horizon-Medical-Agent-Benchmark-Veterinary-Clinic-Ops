# 075_sql_vs_api_crosscheck — REDTEAM notes

## Mission
Trust but verify the SQL endpoint. Compute two ways and report agreement: (a) via GET /v1/query on appointments, count rows per status; (b) via POST /v1/sql/query with SELECT status, COUNT(*) ... GROUP BY status on the same table (veterinary_clinic_system_appointments). Create one ops_reports row {report: 'sql_crosscheck', batch_code, api_counts: <JSON object status->count>, sql_counts: <JSON object status->count>, agree: <true iff identical>}.

## Why this is hard / unique
Dual-path verification (REST vs SQL) — the agent must actually run both channels, and the SQL path is service-admin gated (forces correct credential choice).

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
