# 080_enterprise_kpi_pack — REDTEAM notes (Phase 4 PENDING)

## Mission
Generate the enterprise KPI pack for the leadership dashboard as of the episode date. The pack is a 5-row ops_reports write (enterprise, one row per location, and AR aging) with every aggregate recomputed two independent ways (API-filtered Python and SQL). It requires cross-collection reconciliation between boarding_runs and boarding_reservations and correctly handles decoy rows (draft invoice, transferred patient).

## Why this is hard / unique
- Multi-fan-in aggregation across 6+ collections with a single combined end-state.
- Dual-path assertion (Python vs SQL) on every KPI value.
- Reconciliation between the occupancy board and the reservation ledger.
- AR aging with date buckets and strict open-invoice status semantics.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `billing_invoices` id 3 has status='draft' and amount_paid=0; it must not be counted as an open invoice or in AR.
- `patients` id 27 has status='transferred'; it must not be counted as an active patient.
- `boarding_reservations` has only 5 checked_in rows, while the collection has 140 rows; only the checked-in subset reconciles to occupied runs.
- Only `billing_invoices` ids 1 and 2 have status='sent' in the seed; the open-invoice and AR numbers are exactly 2 invoices totaling 737.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
