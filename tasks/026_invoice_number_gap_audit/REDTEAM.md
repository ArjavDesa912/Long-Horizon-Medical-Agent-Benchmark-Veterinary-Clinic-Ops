# 026_invoice_number_gap_audit — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the month-end document control audit for the billing ledgers. Produce a single ops_reports `document_control` row that reports the numeric sequence integrity, distinct owner/patient counts, cross-ledger numeric collisions, and location breakdown for both `billing_invoices` and `billing_estimates`.

## Why this is hard / unique
- Fuses aggregation (sequence parsing and counts) and reconciliation (cross-ledger collision check and location join) into one mission.
- The correct document numbers are `invoice_number` and `estimate_number`, not the row `id`.
- The report requires parsing string prefixes and a join to `locations` for the location_breakdown.
- Dual-path verification: every count and distinct count is recomputed by SQL and raw-row Python.
- The blast radius is only `ops_reports`; every other collection must remain byte-identical.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **id-vs-document-number decoy**: `billing_invoices` row ids are 1..260 and `billing_estimates` row ids are 1..100, while the document numbers are `INV-1001..INV-1260` and `EST-3001..EST-3100`. A solution that uses `id` for min/max/count gets `{invoice_min:1, invoice_max:260, count:260}` and a bogus missing list of 979 numbers instead of the correct `{1001, 1260, '', true}`.
- **Status decoy**: Both ledgers contain rows in every status (invoices: 257 paid, 2 sent, 1 draft; estimates: 40 sent, 30 draft, 20 accepted, 10 declined). The count and sequence must include all rows, not just a subset. Excluding the draft invoice would reduce the count to 259 and create a gap at `INV-1003`.
- **No cross-collision trap**: The invoice suffix range 1001..1260 and the estimate suffix range 3001..3100 do not overlap, so `cross_collisions` should be `[]`. A solution that compares suffixes without prefixes will still find none, but a hardcoded `[]` would fail if a future reseed creates an overlap.
- **Location join**: `billing_invoices.location_id` and `billing_estimates.location_id` are string foreign keys (`'1'`, `'2'`, `'3'`). The breakdown must use `locations.name` (Main Street Animal Hospital, Riverside Veterinary Clinic, Cedar Park Animal Care Center), not the raw `location_id`.
- **Distinct counts**: Invoices have 220 distinct `owner_id` values and 260 distinct `patient_id` values; estimates have 100 distinct `owner_id` and 100 distinct `patient_id`. These must be derived from live rows, not hardcoded.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
