# 019_run_status_audit — REDTEAM notes

## Mission
The occupancy board and the reservation book disagree somewhere. A run is consistent iff: (status 'occupied' <=> there is a checked_in reservation on that run) AND (occupied runs have current_patient_id equal to that reservation's patient) AND (non-occupied runs have no current_patient_id). Find every inconsistent run and repair the RUN side only: set status 'occupied' + correct current_patient_id where a checked_in reservation exists; otherwise set status 'available' and current_patient_id null (unless the run is 'cleaning' with no occupant — leave those as 'cleaning'). Never edit reservations. Record your work: add field audited='<batch_code>' to every run you changed.

## Why this is hard / unique
Bidirectional invariant repair (both false-occupied and false-available directions) with a leave-cleaning-alone exception; symptom-not-rows phrasing.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
