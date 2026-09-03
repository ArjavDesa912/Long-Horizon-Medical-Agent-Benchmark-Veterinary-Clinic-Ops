# 092_idempotent_occupancy_sync — REDTEAM notes

## Mission
Sync the boarding board so runs exactly mirror the reservation book, idempotently: after your changes, a run must be 'occupied' with current_patient_id set IFF a checked_in reservation references it (patient from that reservation); runs with no checked_in reservation must be 'available' with current_patient_id null — EXCEPT runs whose status is 'maintenance', which stay 'maintenance' with null occupant. Add field synced='<batch_code>' ONLY to runs you actually changed. Running the sync twice must change nothing the second time (the tag must already match the current batch_code — do not re-stamp).

## Why this is hard / unique
Convergent sync with change-only tagging — second-run no-op is directly verified; over-eager re-tagging fails.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
