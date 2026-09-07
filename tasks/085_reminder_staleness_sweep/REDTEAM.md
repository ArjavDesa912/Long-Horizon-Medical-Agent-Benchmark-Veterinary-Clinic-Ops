# 085_reminder_staleness_sweep — REDTEAM notes (Phase 4 PENDING)

## Mission
Dismiss queued reminders older than 14 days before the episode date, send a dismiss-notice communication to the resolved owner (via patients for vaccination/boarding reminders, from the queue for invoice reminders), log the sweep to audit_log, and create an ops_reports summary with batch code, dismissed count, by-kind breakdown, and sorted dismissed ids.

## Why this is hard / unique
- The staleness predicate is on `queued_at`, not `due_date`, and must be computed against the episode nonce.
- Owner resolution requires a patient join for two of the three stale reminders; the queue rows have `owner_id=null`.
- The mission spans four write collections (reminder_queue, communications, ops_reports, audit_log) and requires idempotent delete-then-rewrite for the report.
- Dual-path verification (raw-row filter vs SQL) on every derived count.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `reminder_queue` id=3: `kind='invoice_overdue'`, `status='sent'`, `queued_at='2026-09-01T21:08:41.265+00:00'`. This is older than the stale threshold but not `queued`; a status-agnostic "dismiss old rows" solution will touch it and fail the row-equality canary.
- `reminder_queue` id=2: `kind='vaccination_due'`, `status='queued'`, `queued_at='2026-09-04T21:08:41.265+00:00'`, `due_date='2026-09-10T00:00:00+00:00'`. The `due_date` is in the future, but `queued_at` is stale. A solution that uses `due_date` as the staleness clock acts on the wrong predicate.
- `reminder_queue` id=4: `kind='boarding_checkin'`, `status='queued'`, `queued_at='2026-09-04T21:08:41.265+00:00'`, `patient_id='8'`. This is a non-vaccination queued reminder that is also stale; a solution that only sweeps `vaccination_due` reminders misses it.
- Stale reminders ids 1 and 2 have `patient_id='2'` and `'5'` with `owner_id=null`; id=4 has `patient_id='8'`. `patients` records show patient 2 → owner 1, patient 5 → owner 3, patient 8 → owner 5. Reading `owner_id` directly from the queue row for these would yield null.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
