# 041_noshow_fee_flag — REDTEAM notes (Phase 4 PENDING)

## Mission
Charge a flat $25 no-show fee for every missed appointment. Set `follow_up='call_owner'` on each no_show, create a batch-keyed billing invoice, log an audit row, and produce a per-location `ops_reports` summary.

## Why this is hard / unique
- Cross-collection workflow: appointments -> billing_invoices -> audit_log -> ops_reports.
- Requires a patient-to-owner join (appointments do not carry `owner_id`).
- Batch-keyed invoice numbering is required for idempotency and rerun safety.
- Derived summary numbers (total no-shows, total fees, per-location counts) are dual-path verified.
- Existing billing invoices must remain byte-identical.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- 66 no_show appointments exist; the other ~482 appointments must remain untouched.
- No-show dates are all in the past (2026-08-05 to 2026-09-03), so a future-only filter fails.
- The $25 fee is a flat policy value; fee_schedules contains WELL-EXAM ($62) and SICK-EXAM ($85), which are decoy amounts.
- Patient-to-owner join is required: appointments lack `owner_id`; patient id=80 has owner_id=128, id=187 has owner_id=102, etc.
- Existing `billing_invoices` has 260 rows (INV-1001...INV-1260) that must not be modified.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
