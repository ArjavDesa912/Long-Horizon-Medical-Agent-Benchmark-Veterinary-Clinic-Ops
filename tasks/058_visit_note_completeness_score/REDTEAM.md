# 058_visit_note_completeness_score — REDTEAM notes

## Mission
Score documentation quality. A visit record is 'complete' iff subjective, objective, assessment, and plan are all non-empty strings AND weight_kg is a positive number. Create one ops_reports row {report: 'note_completeness', batch_code, total_visits, complete, incomplete, completeness_pct: <round(100*complete/total,1)>, incomplete_ids: <comma-joined ascending ids of incomplete rows, or ''>}.

## Why this is hard / unique
Multi-clause completeness predicate + an id listing that must be sorted — agents emit unsorted ids or off-by-one predicates.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
