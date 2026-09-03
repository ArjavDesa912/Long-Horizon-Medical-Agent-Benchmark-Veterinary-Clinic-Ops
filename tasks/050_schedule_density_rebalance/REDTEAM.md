# 050_schedule_density_rebalance — REDTEAM notes

## Mission
Balance the books at location 1. Find the future date (on/after episode date) with the most scheduled-or-confirmed appointments at location 1 — the 'overloaded' day (tie -> earliest date). If that day has strictly more than 4 such appointments, move its LATEST-starting scheduled appointment to the future date at location 1 with the FEWEST scheduled-or-confirmed appointments (tie -> earliest date), keeping the same start_time/end_time/room, and set rebalanced='<batch_code>' on the moved row. If no day exceeds 4, change nothing and instead create an ops_reports row {report: 'rebalance', batch_code, moved: 0}.

## Why this is hard / unique
Two arg-extremes with deterministic tiebreaks and a conditional no-op branch — agents must evaluate the guard, not assume it fires.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
