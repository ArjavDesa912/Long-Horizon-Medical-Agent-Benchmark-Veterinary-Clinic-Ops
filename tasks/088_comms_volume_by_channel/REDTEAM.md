# 088_comms_volume_by_channel — REDTEAM notes

## Mission
One ops_reports row {report: 'comms_channels', batch_code, by_channel: <JSON object channel -> count over all communications>, by_direction: <JSON object direction -> count>, total: <rows>}.

## Why this is hard / unique
Dual-axis count distribution in nested JSON.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
