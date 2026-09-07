# 093_idempotent_invoice_numbering — REDTEAM notes (Phase 4 PENDING)

## Mission
Backfill the canonical public reference `PUB-<invoice_number>` on all 260 billing_invoices, leaving already-correct rows byte-identical, and upsert one ops_reports `public_ref_backfill` row for the batch. Second run must change zero invoices and report `backfilled: 0`.

## Why this is hard / unique
- 10x volume means a bulk backfill over 260 rows; brute-force manual inspection is infeasible.
- The public_ref must be derived from invoice_number, not id, and the offset (id 1 == INV-1001) must be respected.
- Idempotency: no-op on already-correct rows is enforced by byte-identity (ignoring public_ref and updated_at for changed rows, but everything else must match).
- Aggregate report must be upserted by batch_code, not duplicated on rerun.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- All 260 invoices (id 1-260, invoice_number INV-1001..INV-1260) have public_ref null in the snapshot, so the expected backfill count is 260.
- Hardcoding a count, reading only a page, or deriving public_ref from id rather than invoice_number will fail.
- Updating already-correct rows causes updated_at drift and fails byte-identity.
- Pushing a second ops_reports row on rerun creates a duplicate; the report must be upserted by batch_code.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
