# 005_vaccine_lot_recall_trace — REDTEAM notes

## Mission
The manufacturer recalled one vaccine lot: the lot_number that appears most frequently across all vaccination records is suspect (break a tie by choosing the alphabetically smallest lot_number). Find every patient who received that lot, and for each affected patient's owner push one communications row with channel='phone', direction='outbound', subject='Vaccine lot recall — <lot_number>', body='Recall callback scheduled for <PatientName> (lot <lot_number>).', logged_by='Dr. Alvarez', and occurred_at on the episode date. One row per affected patient (not per vaccination). Do not touch any seeded communications.

## Why this is hard / unique
Mode-with-tiebreak aggregation + distinct-patient fan-out through a patient→owner join; off-by-one duplicates are the common failure.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
