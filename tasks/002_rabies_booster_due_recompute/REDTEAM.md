# 002_rabies_booster_due_recompute — REDTEAM notes (Phase 4 PENDING)

## Mission
A data-import glitch corrupted the due_date on every canine rabies vaccination. Recompute each one from the AAHA canine rabies booster interval (1 year after administered_date), then run the full batch audit: due-date fix, reminders and owner communications for patients whose new due date is within 30 days or overdue, ops_reports batch summary with inventory coverage, and an audit_log entry. The task is idempotent and uses dual-path verification for all aggregates.

## Why this is hard / unique
- Species-specific rule must be derived (canine 1-year rabies booster) and applied only to the correct subset.
- Multi-collection batch audit requires correct sequencing and idempotent writes across `vaccinations`, `reminder_queue`, `communications`, `ops_reports`, and `audit_log`.
- Dual-path verification: every aggregate (total, overdue, due_next_30, current, on_hand, reminder count) is computed both by Python and by independent SQL.
- Real red-herring rows: feline/avian/exotic/equine rabies rows, non-rabies canine rows, and unrelated reminder_queue kinds.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Non-canine rabies decoys** — 45 feline rabies rows (e.g. row id 9 for patient 5/Clementine), 7 avian, 9 exotic, 7 equine. Verified by filtering `vaccinations.vaccine_type='rabies'` against `patients.species`.
2. **Non-rabies canine decoys** — row id 2 for patient 1/Biscuit is DHPP, not rabies. Any `species='canine'` filter alone over-writes these.
3. **Unrelated queued reminders** — `reminder_queue` id 3 (`invoice_overdue`, `status='sent'`) and id 4 (`boarding_checkin`, `status='queued'`) are decoys that must survive byte-identical.
4. **Date-boundary jitter** — the episode date is not in the seed snapshot, but the live `ops_meta.episode_date` is used; the counts of overdue/due_next_30/current change with it, preventing hardcoded answers.
5. **Multi-pet owners** — some owners have multiple canine patients; `patient_id` is the required key on communications/reminder_queue, not owner_id or text.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships.
