# 081_reminder_template_render — REDTEAM notes

## Mission
Render the seeded 'Vaccination overdue (SMS)' reminder template for every patient with an overdue vaccination (due_date strictly before the episode date) who is NOT already in the queue with a queued vaccination_due row. Substitute {{patient_name}}, {{vaccine_type}}, {{due_date YYYY-MM-DD of the patient's oldest overdue vaccination}}, and {{clinic_phone}} with the phone of the LOCATION the patient belongs to. Push one row per patient: {kind: 'vaccination_due', patient_id, due_date: <oldest overdue due_date>, message: <rendered template>, status: 'queued', queued_by: 'system', queued_at: episode timestamp}.

## Why this is hard / unique
Template rendering with a multi-source substitution map (patient + vaccination + location phone); agents hardcode the phone or use the wrong due date.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
