# 003_vaccination_reminder_batch — REDTEAM notes

## Mission
Do exactly what the 'Send Reminder' button on the Patients → Vaccinations screen is for: enqueue one reminder_queue entry for every patient whose latest-due vaccination of any type is overdue as of the episode date in ops_meta. Each new row must have kind='vaccination_due', the patient_id, due_date set to that patient's most-overdue due_date, status='queued', queued_by='admin@pawsclinic.com', queued_at set to the episode timestamp (any time on the episode date), and a message of the form '<PatientName> is overdue for <vaccine_type> — call to book a nurse visit.' Use each patient's earliest (oldest) overdue due_date when several vaccines are overdue. Do not modify or delete the four seeded reminder_queue rows, and do not create duplicates for patients who already have a queued vaccination_due reminder.

## Why this is hard / unique
Anti-duplication against seeded queue + earliest-due selection per patient mirrors the real Send Reminder pipeline; message template must match exactly, forcing instruction-following rather than guessing.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
