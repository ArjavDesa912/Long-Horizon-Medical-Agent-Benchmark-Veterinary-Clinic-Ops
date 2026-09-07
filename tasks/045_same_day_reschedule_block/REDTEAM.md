# 045_same_day_reschedule_block — REDTEAM notes (Phase 4 PENDING)

## Mission
Dr. Priya Natarajan (provider id 3) has called in sick. The task is a fused workflow: reassign every scheduled appointment of provider 3 on/after the episode date to the covering provider 4 with `covering_for='3'`; for any of those that fall on the episode date itself, also push one outbound SMS communication to the owner and one `appointment_reschedule` reminder_queue row. Confirmed, past, completed, no_show, checked_in, and other providers' appointments must remain untouched.

## Why this is hard / unique
- **Implicit status filter**: the rule is `scheduled` only, but the natural first instinct is "move all of provider 3's future appointments". Confirmed future appointments are planted decoys.
- **Date boundary + same-day artifact**: the same-day subset triggers extra communication and queue rows; an off-by-one boundary changes which rows get those artifacts.
- **Multi-collection blast radius**: appointments, communications, and reminder_queue all change, but seeded rows in each must survive unchanged.
- **Idempotency**: a second run must delete the batch's own prior comms/reminders and re-create them to the same end-state.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Provider 3 confirmed future/same-day decoys: e.g., row id 39 (`provider_id='3'`, `status='confirmed'`, `appointment_date='2026-09-27'`), id 112 (`provider_id='3'`, `status='confirmed'`, `appointment_date='2026-09-30'`), id 205 (`2026-09-29 confirmed`), id 330 (`2026-10-02 confirmed`), id 392 (`2026-10-01 confirmed`), id 519 (`2026-09-30 confirmed`).
- Provider 3 scheduled past decoys: e.g., row id 10 (`provider_id='3'`, `status='scheduled'`, `appointment_date='2026-09-04'`), id 26 (`scheduled`, `2026-09-20`), id 32 (`scheduled`, `2026-09-17`).
- Other-provider decoys: e.g., id 35 (`provider_id='4'`, `status='scheduled'`, `2026-10-01`), id 133 (`provider_id='1'`, `status='scheduled'`, `2026-09-27`).
- Unrelated reminder_queue rows: id 1 (`vaccination_due`, queued), id 2 (`vaccination_due`, queued), id 3 (`invoice_overdue`, sent), id 4 (`boarding_checkin`, queued) must not be touched.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
