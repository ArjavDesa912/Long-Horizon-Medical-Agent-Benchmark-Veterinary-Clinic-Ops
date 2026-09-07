# 023_late_fee_assessment — REDTEAM notes (Phase 4 PENDING)

## Mission
Apply a per-episode late fee to overdue invoices. The percentage is read from ops_meta.late_fee_pct (3-9). For every invoice with status='overdue' or status='sent' and due_date strictly before the episode date, and with unpaid balance > 0: re-flag the invoice as overdue, append a late-fee line item, increase the invoice total and the owner's balance, email the owner, append an audit entry, and push a summary ops_report. Paid and draft invoices are never touched. The pass must be idempotent.

## Why this is hard / unique
- The late-fee percentage is per-episode metadata, not a hardcoded constant, so the fee amount and the line-item description text both change every reset.
- The task modifies nested line_items (append-only), invoice totals, owner balances, communications, audit_log, and ops_reports.
- Fee rounding is standard half-up to cents; the verifier compares exact cents.
- The rule must handle invoices that are already 'overdue' at seed as well as 'sent' past-due invoices (the seed has none of the former, but the verifier does).
- Idempotency is non-trivial: a re-run must not append a second late-fee line item, double an owner balance, or duplicate communication/audit rows.
- Dual-path verification on target count, pre-fee unpaid, post-fee unpaid, total fees, new invoice totals, and per-owner/per-location fee splits.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Percentage decoy: ops_meta.late_fee_pct is randomized per episode. A hardcoded 5% only matches one possible value; any other value makes every line-item description and balance wrong.
- Status decoy: at seed there are no 'overdue' invoices, only 'sent' past-due invoices (ids 1 and 2). A solution that only looks for status='overdue' does nothing.
- Draft decoy: billing_invoices id 3 (INV-1003, status='draft', due 2026-09-23, owner 3) is past the default episode but must not be touched because it is not an open AR invoice.
- Paid decoys: the remaining 257 invoices have status='paid' and must remain byte-identical. A bulk 'add late fee where due<ep' would corrupt these.
- Owner-balance trap: the two target owners (1 and 2) have positive balances but they are not equal to the invoice unpaid amounts; the fee must be added to the existing balance, not set to the fee.
- Rounding trap: with pct 3 on $523.00 the fee is $15.69, not $15.68 or $15.70. The verifier uses Decimal half-up rounding.
- Idempotency trap: the late-fee line item has the exact description `Late fee (<pct>% of overdue balance)`. A re-run must detect this and skip the invoice.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
