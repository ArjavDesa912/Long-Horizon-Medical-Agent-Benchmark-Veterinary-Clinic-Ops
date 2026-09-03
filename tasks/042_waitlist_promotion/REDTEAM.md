# 042_waitlist_promotion — REDTEAM notes

## Mission
A cancellation opened a slot: location 1, Exam 1, the episode date at 09:00–09:30 with Dr. Elena Alvarez (provider id 1). Promote the HIGHEST-priority waiting waitlist entry at location 1 (priority order: urgent > work_in > routine; break ties by earliest created_at) into a real appointment: create the appointment {patient_id from the waitlist entry, provider_id '1', location_id '1', room 'Exam 1', appointment_date = episode date, start_time '09:00', end_time '09:30', reason = the waitlist entry's reason, status 'scheduled'}, and set that waitlist entry's status to 'booked'. Other waitlist entries stay 'waiting'.

## Why this is hard / unique
Priority-rank ordering with a timestamp tiebreak; agents often take the first row or use wrong rank order.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
