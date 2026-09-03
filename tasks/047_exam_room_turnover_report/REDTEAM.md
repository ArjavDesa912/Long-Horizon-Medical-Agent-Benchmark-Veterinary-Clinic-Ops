# 047_exam_room_turnover_report — REDTEAM notes

## Mission
Which exam rooms carried the load? One ops_reports row {report: 'room_usage', batch_code, per_room: <JSON object mapping room name -> total appointment count across ALL appointments at all locations>, busiest_room: <room with the most appointments; tie -> alphabetically first>}. Exactly one row.

## Why this is hard / unique
Nested-JSON report field with deterministic tiebreak; tests structured-output fidelity.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
