# 065_deceased_patient_archive — REDTEAM notes

## Mission
Patient 17 (Rocket) has passed away. Archive properly: (1) set the patient's status to 'deceased' and add field archived='<batch_code>'; (2) cancel any of his 'reserved' boarding reservations (status 'cancelled', cancellation_reason 'patient_deceased'); (3) remove his 'waiting' waitlist entries (delete them); (4) cancel his future appointments (status 'scheduled' or 'confirmed' with appointment_date on/after the episode date -> status 'cancelled'). Completed and past records are history — never alter them.

## Why this is hard / unique
Cross-collection cascaded archival where each target collection has a different correct action (update vs cancel vs delete).

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
