# 100_grand_daily_closeout — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the grand end-of-day closeout for the practice: convert accepted estimates into sent invoices, reflag sent invoices whose due date is past the episode date as overdue, flush all queued reminders, create missing boarding daily logs for checked-in reservations, write a summary `ops_reports` row, and append a `DAILY_CLOSEOUT` audit row. Every count in the summary and audit must agree with the live-derived totals.

## Why this is hard / unique
- **Six-step composite workflow**: touches `billing_estimates` (read), `billing_invoices` (insert + update), `reminder_queue` (update), `boarding_daily_log` (upsert), `ops_reports`, and `audit_log`.
- **Idempotent counts**: the summary numbers are derived from the pre-episode state (accepted estimates, sent/overdue invoices with due<ep, queued reminders, checked-in reservations minus preexisting episode logs) so a second run reaches the same report even after rows have changed.
- **Multiple decoy rows**: accepted vs. sent/declined/draft estimates, draft vs. sent/paid invoices, queued `boarding_checkin` vs. `vaccination_due` reminders, existing vs. missing daily logs.
- **Self-consistency verification**: the `ops_reports` and `DAILY_CLOSEOUT` audit numbers are checked against independent SQL and raw-row recomputations.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `billing_estimates`: 20 accepted rows (ids 5,6,15,16,25,26,35,36,45,46,55,56,65,66,75,76,85,86,95,96); 80 non-accepted rows.
- `billing_invoices`: id=1 and id=2 are `status='sent'` (due 2026-08-21 and 2026-09-20); id=3 is `status='draft'`.
- `reminder_queue`: id=1,2 queued `vaccination_due`; id=4 queued `boarding_checkin`; id=3 `sent` `invoice_overdue`.
- `boarding_reservations`: id=1-5 are `checked_in`; id=6-140 are `reserved` or `checked_out`.
- `boarding_daily_log`: rows 1-10 cover reservations 1-5 on `2026-09-03` and `2026-09-04`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
