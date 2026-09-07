# 024_estimate_to_invoice_conversion — REDTEAM notes (Phase 4 PENDING)

## Mission
Convert every accepted estimate into a sent invoice with net-21 terms. For each accepted estimate: create a new invoice with a nonce-embedded number, copy owner/patient/location/line_items/total, set amount_paid=0 and status='sent'; set the estimate status to 'converted'; email the owner; append an audit entry; then push a summary ops_report. Estimates with any other status stay untouched.

## Why this is hard / unique
- Multi-collection write workflow: billing_estimates, billing_invoices, communications, audit_log, ops_reports.
- Per-episode nonce and date are embedded in invoice numbers, due dates, communication subject/body, audit details, and the summary report.
- The snapshot has 100 estimates but only 20 are accepted at 10x seed; converting the wrong status corrupts the ledger.
- Idempotency is required: a re-run must not duplicate invoices, communications, or audits, and must overwrite the same ops_report row.
- Dual-path Python/SQL aggregate verification on accepted count, total converted, and per-location totals.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Scale decoy: 100 estimates, only ~20 accepted. A status filter must be exact (`status='accepted'`).
- Numbering collision: invoice numbers use `INV-C<batch_code>-<estimate digits>`. The batch code changes per episode, and the digits come from the estimate_number (e.g. EST-3005 -> 3005). Hardcoded numbers fail.
- Date decoy: issued_date is the episode timestamp and due_date is episode + 21 days. Using estimate.created_date or expires_date fails.
- Owner/patient/location copy: the new invoice must copy the estimate fields exactly. Re-deriving owner from patient could fail if the owner_id stored on the estimate differs from the patient's owner (it matches in the seed, but the rule is copy).
- Line-item and total preservation: line_items and total_amount must be copied exactly; changing unit_price or quantity fails.
- Duplicate-creation trap: a re-run must detect that the invoice already exists (by invoice_number) and not create a duplicate. The estimate status is already 'converted', so re-updating is harmless but a second invoice creation is fatal.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
