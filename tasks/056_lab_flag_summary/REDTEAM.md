# 056_lab_flag_summary — REDTEAM notes

## Mission
One ops_reports row {report: 'lab_flags', batch_code, critical: <count of lab_results with flag 'critical'>, abnormal: <count 'abnormal'>, normal: <count 'normal'>, total: <all rows>}.

## Why this is hard / unique
Baseline distribution report; ensures the ops_reports channel is exercised with exact counts.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
