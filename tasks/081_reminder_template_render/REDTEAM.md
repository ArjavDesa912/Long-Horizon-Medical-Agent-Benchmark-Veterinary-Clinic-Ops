# 081_reminder_template_render — REDTEAM notes (Phase 4 PENDING)

## Mission
Render and queue a two-channel vaccination reminder campaign (SMS for overdue, email for upcoming) using the live `reminder_templates`, the live patient/location/vaccination data, and the existing `reminder_queue` for deduplication.

## Why this is hard / unique
- Two live templates with different substitution sets (SMS adds `clinic_phone`).
- Two non-overlapping patient windows (overdue vs upcoming) plus existing-queue deduplication.
- Location-specific phone substitution.
- Exact message rendering verification with patient_id-level matching.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `reminder_queue` ids 3 and 4 are non-vaccination_due rows (invoice_overdue, boarding_checkin); they must not be modified.
- `reminder_queue` ids 1 and 2 are already-queued vaccination_due rows for patients 2 and 5.
- Patients can share names, so matching by `(patient_id, message)` is required.
- `locations` phones are location-specific; loc 1/2/3 have distinct phone numbers.
- Date boundary: `due_date < episode_date` is overdue; `episode_date <= due_date <= episode_date + 7` is upcoming.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks before this task ships.
