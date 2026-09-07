# 012_boarding_checkout_cleaning_cycle — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the evening checkout and cleaning cycle. For every checked_in reservation whose check_out is on or before the episode date, check it out, set its run to cleaning with the occupant cleared, create a boarding invoice from the fee schedule, send the owner an email, and push a checkout manifest in `ops_reports`.

## Why this is hard / unique
- Multi-guest checkout with invoice generation and run-state machine.
- Fee-schedule join required to compute the correct invoice total.
- Run must be 'cleaning' after checkout, not immediately 'available'.
- Dual-path verification of total nights and total revenue.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Date ordering and scope**: the five checked_in guests have check_out dates 2026-09-06 (three guests), 2026-09-07, and 2026-09-09. They must be processed in ascending `(check_out, id)` order.
- **Run state machine**: runs must become `cleaning` with `current_patient_id` cleared. A shortcut to `available` fails.
- **Fee schedule lookup**: every location's fee schedule has a `BOARD-NIGHT` item priced at 38, but the invoice must be derived from that live data, not a hardcoded constant.
- **Invoice and communication deduplication**: `invoice_number` and email subject are keyed by the live `batch_code`, so a second run must skip existing invoices and emails and overwrite the manifest row.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
