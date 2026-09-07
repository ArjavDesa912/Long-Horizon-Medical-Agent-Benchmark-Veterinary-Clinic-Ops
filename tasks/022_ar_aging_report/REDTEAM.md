# 022_ar_aging_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Build the month-end AR aging and owner-balance reconciliation pack. Compute AR aging buckets (0-30, 31-60, 61-90, 90+) for open invoices, write per-location aging rows, produce a reconciliation summary that compares each owner's balance to their ledger open AR, and append an audit entry. No source collection may be modified.

## Why this is hard / unique
- Report-only mission that requires touching 6+ collections (billing_invoices, owners, patients, locations, ops_reports, audit_log) without mutating the source data.
- The open AR set is only 2 invoices in a 260-row ledger, so the agent must correctly exclude paid and draft invoices.
- AR aging buckets shift with episode jitter, requiring date arithmetic.
- Owner-balance reconciliation is a genuine multi-hop join and aggregate: 58 of 220 owners have a balance/open-AR mismatch, and the task is to report, not fix.
- Dual-path verification on every aggregate (bucket totals, per-location open, per-owner open, total open AR, total owner balance).

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Draft decoy: billing_invoices id 3 (INV-1003, status='draft', issued 2026-09-02, unpaid $546) must be excluded from AR aging because the rule is status 'sent' or 'overdue'.
- Paid decoys: 257 paid invoices have zero unpaid and must be excluded.
- Jitter-sensitive buckets: the two open invoices (id 1 issued 2026-07-31 and id 2 issued 2026-08-30) change buckets as the episode date jitters ±3 days around 2026-09-30. At 2026-09-30, id 1 is 61 days (61-90) and id 2 is 31 days (31-60); at 2026-09-27, id 1 is 58 days (31-60) and id 2 is 28 days (0-30); at 2026-10-03, id 1 is 64 days (61-90) and id 2 is 34 days (31-60).
- Owner/ledger drift: 58 owners mismatch their open AR. The breakdown is 55 owners with positive balance and zero open AR, owner 1 (balance $134.00, open AR $523.00), owner 2 (balance $0.00, open AR $214.00), and owner 21 (balance -$45.00, open AR $0.00). A solution that "fixes" owner balances instead of reporting the discrepancy would modify a non-blast collection and fail the canary.
- Idempotency: the three report rows and the audit row are keyed by batch_code; a re-run must overwrite and not duplicate.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
