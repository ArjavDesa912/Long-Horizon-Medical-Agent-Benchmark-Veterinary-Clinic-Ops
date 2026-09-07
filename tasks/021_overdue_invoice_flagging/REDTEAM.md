# 021_overdue_invoice_flagging — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the month-end overdue invoice flagging and owner outreach pass: re-flag sent past-due invoices as overdue, enqueue an invoice_overdue reminder for each, email the owner, append an audit entry, and push a summary ops_report. The pass must be idempotent and leave paid/draft/future-due invoices untouched.

## Why this is hard / unique
- Multi-collection workflow spanning billing_invoices, reminder_queue, communications, audit_log, and ops_reports.
- The business rule is a status migration triggered by a strict due-date comparison, not a single table update.
- Day-count and unpaid-balance are embedded in three different human-readable strings (reminder.message, communications.body, audit_log.details); exact formatting is checked.
- Target set is only 2 rows in the 260-row invoice ledger, so an over-broad filter touches 257 paid decoys.
- Dual-path aggregate verification on count, total unpaid, and per-location unpaid.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Draft decoy: billing_invoices id 3 (INV-1003, status='draft', due 2026-09-23, owner 3) is past the default episode but must not be touched because it is not 'sent'.
- Paid decoys: the remaining 257 invoices have status='paid' and must remain byte-identical. A bulk 'set status=overdue where due<ep' would corrupt these.
- Target rows: only ids 1 (INV-1001, owner 1, patient 1, due 2026-08-21) and 2 (INV-1002, owner 2, patient 2, due 2026-09-20) are 'sent' and past due at 2026-09-30, both with unpaid balances >0.
- Age N is jitter-sensitive: at 2026-09-30 invoice 1 is 40 days overdue and invoice 2 is 10 days overdue; at 2026-09-27 these are 37 and 7. Hardcoded day counts or message text fail.
- Duplicate-prevention: a re-run must not create duplicate reminder/communication/audit rows for the same invoice. The verifier enforces exactly one row per target keyed by the natural composite keys.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
