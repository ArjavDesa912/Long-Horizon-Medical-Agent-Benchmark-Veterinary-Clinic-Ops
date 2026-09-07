# 016_boarding_stay_invoice_draft — REDTEAM notes

## Mission
Close out and draft invoices for all checked-in boarding stays whose check_out is on or before the episode date. For each stay: flip the reservation to 'checked_out', free the run, create a draft invoice with a batch-embedded invoice number and a BOARD-NIGHT line item, push a closeout audit_log entry, and summarize everything in a 'boarding_closeout' ops_reports row.

## Why this is hard / unique
- Multi-hop derivation: nights come from reservation dates, unit_price from the location's fee_schedule, owner from the patient, and the run_type from the boarding_runs record.
- Net-21 due date is domain knowledge the agent must apply, not read directly.
- Revenue and run-status aggregates are verified two independent ways (Python path vs SQL SUM/GROUP BY).
- The blast radius includes 5 collections, but the mission reads from 9+.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Only reservations 1-5 are checked_in at default ep; all other reservations (113 checked_out, 22 reserved) must not be billed or checked out.
- Reservations 3 and 4 share runs with future reserved bookings (99 and 98), so a solution that flips every reservation on an occupied run over-bills.
- Pre-existing invoices (260) include 67 with boarding line items; a solution that looks for any invoice with 'Boarding' in the description will confuse itself.
- BOARD-NIGHT price is 38 at every location in the snapshot, but the correct path reads it from the fee_schedule, not hardcodes.
- The due date at default ep 2026-09-30 is 2026-10-21 (ep + 21 days).

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
