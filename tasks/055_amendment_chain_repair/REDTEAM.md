# 055_amendment_chain_repair — REDTEAM notes

## Mission
The immutability rule says locked notes are amended by appending a NEW linked record, never edited. Someone edited locked notes in place: any visit_records row with locked_at set whose updated_at is LATER than its locked_at was tampered with. For each tampered row: leave the row itself alone, but append a correction record {patient_id, provider_id, location_id copied, visit_date = episode date, subjective: 'Amendment of <dp(visit_date)> note: record was modified after locking; content under review.', objective: '', assessment: 'Amendment pending clinical review.', plan: 'Original note quarantined for compliance.', weight_kg copied from the tampered row, problems: [], locked_at: null, amends: <tampered row id as string>, batch: '<batch_code>'}. If no tampered rows exist, do nothing.

## Why this is hard / unique
Forensic detection (updated_at vs locked_at) + append-only correction protocol — the opposite instinct (editing the note) fails.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
