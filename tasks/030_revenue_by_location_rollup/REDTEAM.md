# 030_revenue_by_location_rollup — REDTEAM notes

## Mission
Produce the numbers behind the Revenue by Location report. One ops_reports row per location: {report: 'revenue_by_location', batch_code, location_id, paid_revenue: <sum of amount_paid over that location's PAID invoices, dollars>, open_receivables: <sum of (total_amount - amount_paid) over that location's sent/overdue invoices, dollars>, invoice_count: <all invoices at that location excluding drafts>}. Exactly 3 rows.

## Why this is hard / unique
Mirrors the app's flagship SQL report but must be produced via the plain API; draft exclusion + paid-vs-open split are the traps.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
