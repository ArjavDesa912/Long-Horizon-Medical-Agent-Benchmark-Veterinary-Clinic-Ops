# 025_statement_balance_resync — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the end-of-month accounts-receivable close: age past-due 'sent' invoices to 'overdue', recompute every owner's balance from the live sent/overdue invoice ledger (paid and draft excluded), tag changed owners with the batch nonce, push an `ar_reconciliation` ops_reports row with live per-owner non-zero balances, and send a statement communication to each resynced owner.

## Why this is hard / unique
- Fuses repair (invoice aging + owner balance resync), create (communications + report), and aggregation (AR totals and per-owner balances) into one mission.
- The correct balance for each owner must be derived from only the live open invoice rows; 257 paid invoices and 1 draft invoice are decoys.
- Dual-path verification: every aggregate (open count, overdue count, total AR cents, per-owner AR) is computed via raw-row Python filter and an independent SQL GROUP BY/SUM.
- Idempotency on rerun: the report and communications are overwritten per batch, and owner updates are conditional on a changed balance.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Draft decoy**: `billing_invoices` row id=3 (`invoice_number` `INV-1003`, `owner_id` 3, `total_amount` 546.0, `due_date` 2026-09-23) has status `draft` and a past-due date. The snapshot has exactly 1 invoice with `status='draft'` and 30 estimates with `status='draft'` (for task 028), but only the invoice is in this task's blast radius. A solution that ages or includes draft invoices will overstate AR by $54,600 cents.
- **Paid decoys**: 257 `billing_invoices` rows have `status='paid'` and `amount_paid == total_amount` (zero residual). They are the bulk of the collection and must be ignored in the AR calculation; a solution that includes them would still get the same totals for most owners because their residual is zero, but it would produce the wrong `open_invoice_count` and `overdue_invoice_count` and could mis-age paid rows.
- **Sent-past-due boundary**: The only two `sent` invoices are `INV-1001` (`owner_id` 1, `total_amount` 523.0, `due_date` 2026-08-21) and `INV-1002` (`owner_id` 2, `total_amount` 214.0, `due_date` 2026-09-20). Both are strictly before any allowed episode date (2026-09-27..2026-10-03), so both must flip to `overdue`. A non-strict comparison (`<=` vs `<`) is moot for this seed but is left as a boundary hazard for reseed.
- **Stale owner balances**: `owners` row id=1 has `balance` 134.0 while its open AR is 523.0; id=2 has `balance` 0.0 while its open AR is 214.0. Only these two owners should receive `balance_resynced` and a communication; blanket-tagging all 220 owners fails the `changed <=> tagged` check.
- **ops_reports map**: The `owner_balances` field must contain only non-zero balances. Hardcoding `{1: 523.0, 2: 214.0}` fails on reseed because the amounts derive from `total_amount - amount_paid`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
