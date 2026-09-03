# 052_soap_note_lock_enforcement — REDTEAM notes

## Mission
Enforce the clinic's record-retention rule consistently: clinical notes older than 30 days must be locked (standard medical-records practice — verify if needed). For every visit_records row whose visit_date is more than 30 days before the episode date and whose locked_at is null, set locked_at to the episode timestamp and add lock_reason='retention_policy'. Notes 30 days old or newer, and already-locked notes, stay byte-identical.

## Why this is hard / unique
Threshold boundary (>30, not >=) on a partially-locked collection; agents re-stamp already-locked rows and fail byte-identity.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
