# 027_paid_invoice_receipt_log — REDTEAM notes (Phase 4 PENDING)

## Mission
Log payment receipt confirmations for all paid invoices issued in the two calendar months immediately before the episode month, push an outbound email communication per invoice, and write a `receipt_batch` ops_reports row with counts, total cents, month breakdown, and location breakdown.

## Why this is hard / unique
- Calendar-month window that depends on the per-episode episode_date, not a fixed range.
- Fuses create (communications, report) and aggregation (counts and breakdowns) into one mission.
- Dual-path verification for every aggregate: receipt count, total cents, month breakdown, and location breakdown are computed by raw-row Python and SQL.
- Exact message formatting (money with two decimals, exact subject/body) and one-row-per-invoice semantics.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Calendar-month boundary**: The episode date jitters ±3 days around 2026-09-30. For 2026-09-27..2026-09-30 the target months are 2026-07 and 2026-08, containing 49 paid invoices (25 in Jul, 24 in Aug). For 2026-10-01..2026-10-03 the target months are 2026-08 and 2026-09, containing 24 paid invoices (24 in Aug, 0 in Sep). A rolling 30-day window returns 0 or 1 invoices, and using only the previous month misses half the batch.
- **Non-paid decoys**: `billing_invoices` has 257 `paid` rows, 2 `sent` rows, and 1 `draft` row. Only `status='paid'` rows should generate receipts. A solution that ignores status will pull the two sent and one draft invoice.
- **Money formatting**: `total_amount` is a dollar value (e.g., 523.0). The receipt body must format it with two decimals (`$523.00`). `amount_paid` is not used in the body; the body is a receipt for the full total.
- **occurred_at**: New communications must have `occurred_at` equal to the episode timestamp. Using the `issued_date` or a hardcoded date fails.
- **One row per invoice, not per owner**: In this seed every target owner has exactly one invoice in the window, but the code must not collapse by owner; the verifier checks the count and each receipt individually.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
