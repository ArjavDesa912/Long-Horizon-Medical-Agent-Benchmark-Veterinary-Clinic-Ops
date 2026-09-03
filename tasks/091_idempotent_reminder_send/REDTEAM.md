# 091_idempotent_reminder_send — REDTEAM notes

## Mission
Run the vaccination reminder batch such that running it TWICE is safe. For each patient with an overdue vaccination (due_date strictly before episode date) and no existing reminder_queue row with dedupe_key='vac-<patient_id>-<batch_code>', push one row {kind: 'vaccination_due', patient_id, due_date: <oldest overdue due>, message: 'Overdue vaccination reminder <batch_code>', status: 'queued', queued_by: 'system', queued_at: episode timestamp, dedupe_key: 'vac-<patient_id>-<batch_code>'}. Rows that already carry the dedupe_key must not be duplicated or modified.

## Why this is hard / unique
Explicit idempotency key discipline; verifier runs the gold twice to prove no duplication — agents that blind-insert fail the second pass.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
