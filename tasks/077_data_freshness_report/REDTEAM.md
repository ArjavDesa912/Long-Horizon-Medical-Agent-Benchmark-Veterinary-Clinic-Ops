# 077_data_freshness_report — REDTEAM notes

## Mission
How stale is each collection? One ops_reports row {report: 'data_freshness', batch_code, oldest_collection: '<short name (without prefix) of the collection whose newest updated_at is oldest>', newest_collection: '<short name whose newest updated_at is newest>', checked: <number of collections checked>}. Consider all 24 seeded collections (exclude ops_meta and ops_reports).

## Why this is hard / unique
Meta-aggregation across ALL collections (24 queries); agents check only the collections they already know.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
