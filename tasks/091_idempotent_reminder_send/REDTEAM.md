# 091_idempotent_reminder_send — REDTEAM notes (Phase 4 PENDING)

## Mission
Idempotently enqueue one overdue-vaccination reminder per overdue patient for the current batch, using each patient's earliest overdue due date and a batch-scoped dedupe_key, then write an aggregate ops_reports summary that is correct on both first and second runs.

## Why this is hard / unique
- Overdue set must be derived from 600 vaccination rows with strict date boundary `<` against a jittered episode date.
- Pre-existing queue rows include non-vaccination decoys and queued vax rows without dedupe_keys; both are canary hazards.
- The aggregate report count must be re-derived from the post-mutation state, not a run-local delta, so it stays correct when run twice.
- Dual-path verification (Python filter vs SQL GROUP BY/MIN) on the overdue patient set and earliest due dates.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- reminder_queue seed row id=3 (kind='invoice_overdue', status='sent') and id=4 (kind='boarding_checkin', status='queued') must not be touched.
- reminder_queue seed rows id=1 (patient_id '2') and id=2 (patient_id '5') are queued vax-due but have no dedupe_key; modifying them fails the canary, and skipping all patients with any queued vax-due row undercounts by 2.
- Vaccination rows with due dates in 2026-09-25..2026-10-05 (e.g., id 164 due 2026-09-29, id 204 due 2026-09-30, id 416 due 2026-09-30) straddle the 2026-09-27..2026-10-03 episode jitter window.
- Multiple overdue vaccinations per patient require MIN(due_date), not an arbitrary pick.
- ops_reports does not exist in the snapshot; gold/verifier must tolerate a missing table on first read.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
