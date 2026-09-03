# 070_owner_lifetime_value_report — REDTEAM notes

## Mission
Rank the client base. One ops_reports row per owner: {report: 'owner_ltv', batch_code, owner_id, owner_name, lifetime_revenue: <sum of amount_paid over the owner's PAID invoices, dollars>, open_balance: <sum of (total-paid) over sent/overdue invoices, dollars>, invoice_count: <all non-draft invoices>, pet_count: <patients linked to the owner>}. Include ALL owners, even zeros. Additionally create one row {report: 'owner_ltv_top', batch_code, owner_id, owner_name, lifetime_revenue} for the owner with the highest lifetime_revenue (tie -> lowest owner id).

## Why this is hard / unique
Full-coverage aggregation (zeros included) + a separate argmax row with tiebreak; agents drop zero-owners or mis-tie-break.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
