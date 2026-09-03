# 053_problem_list_rollup — REDTEAM notes

## Mission
Build the practice's chronic-disease census. Across all visit_records' problems arrays, count ACTIVE problems by problem name. Create one ops_reports row per problem name that has at least one active occurrence: {report: 'problem_census', batch_code, problem: <name>, active_cases: <count>, distinct_patients: <count of distinct patient_ids with an active problem of this name>}. Any order; no rows for problems with zero active cases.

## Why this is hard / unique
Nested-array aggregation (problems is a JSON array inside rows) with distinct-patient counting — agents count rows instead of patients.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
