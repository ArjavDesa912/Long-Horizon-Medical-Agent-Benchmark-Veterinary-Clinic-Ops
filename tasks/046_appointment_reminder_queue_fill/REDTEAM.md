# 046_appointment_reminder_queue_fill — REDTEAM notes

## Mission
Tomorrow's appointment reminders, batched. For every appointment with status 'scheduled' or 'confirmed' whose appointment_date equals the episode date + 1 day, push one reminder_queue row: {kind: 'appointment_reminder', patient_id, owner_id: <the patient's owner>, message: 'See you tomorrow at <start_time> for <PatientName>.', status: 'queued', queued_by: 'system', queued_at: episode timestamp, due_date: <the appointment date>}. Skip appointments for patients that already appear in ANY queued reminder_queue row. Seeded rows untouched.

## Why this is hard / unique
Day-precision targeting (exactly tomorrow, not 'future') plus an anti-duplication exclusion against live queue state.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
