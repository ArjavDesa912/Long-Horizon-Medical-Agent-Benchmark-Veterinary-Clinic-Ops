# 090_after_hours_message_log — REDTEAM notes

## Mission
Log an after-hours voicemail: owner id 7 (Frank Kowalski) called about rescheduling. Push one communications row {owner_id: '7', channel: 'phone', direction: 'inbound', subject: 'After-hours voicemail <batch_code>', body: 'Requested reschedule of next appointment; called after closing.', logged_by: 'answering service', occurred_at: episode timestamp}.

## Why this is hard / unique
Simple create with nonce embedding — calibration floor for the create category.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
