# 085_reminder_staleness_sweep — REDTEAM notes

## Mission
Queued reminders go stale. Delete every reminder_queue row with status 'queued' whose queued_at is more than 14 days before the episode date. Rows with other statuses, and fresh queued rows, remain byte-identical.

## Why this is hard / unique
Conditional delete where the predicate uses a timestamp the agent must age against the episode nonce; blanket-deleting queued rows fails.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
