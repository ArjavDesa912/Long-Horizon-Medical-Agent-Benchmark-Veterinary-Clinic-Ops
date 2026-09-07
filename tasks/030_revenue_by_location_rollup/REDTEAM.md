# 030_revenue_by_location_rollup — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the month-end revenue and accounts-receivable aging report by billing location. For each of the three locations, push one `ops_reports` row with paid revenue, open receivables, AR aging buckets, invoice count, distinct patient count, top delinquent patient/owner, and provider count. Append one `audit_log` row documenting the report. All aggregates are verified via dual raw-row and SQL paths.

## Why this is hard / unique
- Multi-hop aggregation and reconciliation across `billing_invoices`, `locations`, `owners`, `patients`, and `providers`.
- `ar_aging` buckets must be derived from `due_date` against the episode date and must sum exactly to `open_receivables`.
- Draft invoices and `billing_estimates` are adversarial decoys; the agent must exclude them from revenue.
- The open receivables are `sent` invoices, not `overdue` status rows, and one is 31-60 days past due while the other is 1-30 days past due.
- `owner.balance` is a decoy; the top delinquent account must come from the unpaid invoice amount.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Draft invoice at location 3**: `billing_invoices.id=3`, `invoice_number=INV-1003`, `status='draft'`, `total_amount=546`, `location_id='3'`. It is the only draft in the snapshot and must be excluded from every aggregate.
- **Only two open invoices, both `sent`**: `billing_invoices.id=1` (`location_id='1'`, `due_date='2026-08-21'`, open `$523.00`) and `id=2` (`location_id='2'`, `due_date='2026-09-20'`, open `$214.00`). There are no `overdue` status rows, so an agent that filters on `status='overdue'` produces `$0` open receivables.
- **Episode-date-driven aging**: base `2026-09-30` with `±3` day jitter in `env.py`. Invoice 1 is always `days_31_60`; invoice 2 is always `days_1_30`. Hardcoded buckets or using `issued_date` fail.
- **Billing location vs. patient home location**: `billing_invoices.id=2` bills to `location_id='2'` but the patient (`patients.id=2`, `name='Pepper'`) has `location_id='1'`. Grouping by `patients.location_id` mis-assigns the second open receivable.
- **Owner balance decoy**: `owners.id=1` `balance=134.0` vs. open invoice `$523.00`; `owners.id=2` `balance=0.0` vs. open invoice `$214.00`. The top delinquent must be derived from the invoice, not `owner.balance`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
