# 046_appointment_reminder_queue_fill — REDTEAM notes (Phase 4 PENDING)

## Mission
Refill the appointment-reminder queue for the next 7 days. Eligible appointments are scheduled/confirmed with appointment_date in [ep+1, ep+7] inclusive, and the patient must not already appear in any queued reminder of any kind. Each row uses the active `appointment_reminder` template's channel, a reason-derived priority (`high` for urgent keywords, `normal` otherwise), and the episode batch code. Seeded reminder_queue rows remain untouched and idempotent re-run is keyed by batch_code.

## Why this is hard / unique
- **Reconciliation with existing queue**: the seed queue already contains queued rows for patients 2, 5, and 8; at some episode dates those patients also have appointments in the 7-day window, so the agent must derive the skip list from live/seed data.
- **Template-driven channel**: the channel is not in the instruction text; it must be read from `reminder_templates`.
- **Reason-based triage priority**: the agent cannot simply copy an appointment priority field; it must inspect the reason string for urgent keywords.
- **Idempotency at 10x volume**: deleting the batch's own previous rows and re-deriving the set prevents double-pushing.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Existing queued reminder patients: row id 1 (patient 2, `vaccination_due`, queued), id 2 (patient 5, `vaccination_due`, queued), id 4 (patient 8, `boarding_checkin`, queued).
- Overlap with the 7-day window for episode 2026-09-27: patient 5 has appointment id 400 on 2026-09-29, patient 8 has appointment id 543 on 2026-09-30.
- Same-day decoys for episode 2026-09-30: id 69 (confirmed, Dental prophylaxis consult), id 112 (confirmed, Skin allergy flare-up), id 125 (scheduled, Vomiting since yesterday) all on 2026-09-30 and must be excluded.
- Stale past-scheduled decoy: id 74 (scheduled, Ear infection re-check, 2026-09-27) is before episode 2026-09-30.
- The active appointment_reminder template is `reminder_templates` id 5 (`trigger='appointment_reminder'`, `channel='sms'`).
- Boundary keyword cases: 'Annual wellness exam' -> routine; 'Vaccine boosters due' -> routine; 'Vomiting since yesterday' -> urgent; 'Ear infection re-check' -> urgent; 'Chronic kidney disease monitoring' -> standard.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
