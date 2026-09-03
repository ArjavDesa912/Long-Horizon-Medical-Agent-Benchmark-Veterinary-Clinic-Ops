# 049_no_show_rate_report — REDTEAM notes

## Mission
One ops_reports row {report: 'no_show_rate', batch_code, past_total: <appointments before the episode date>, past_no_shows: <of those, status 'no_show'>, no_show_pct: <round(100*past_no_shows/past_total, 1)>}.

## Why this is hard / unique
Date-partitioned rate with rounding; trivial-looking but the pct denominator choice (past-only) is the trap.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
