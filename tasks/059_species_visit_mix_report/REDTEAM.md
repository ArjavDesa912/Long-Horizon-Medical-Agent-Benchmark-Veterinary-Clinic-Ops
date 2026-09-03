# 059_species_visit_mix_report — REDTEAM notes

## Mission
Produce the data behind the Visits by Species report. One ops_reports row per species that appears among patients with at least one visit: {report: 'visits_by_species', batch_code, species, visits: <count of visit_records whose patient has that species>, distinct_patients: <distinct patients of that species with visits>, pct_of_visits: <round(100*visits/total_visits,1)>}. Any order.

## Why this is hard / unique
Join-driven aggregation mirroring the app's report screen; species with zero visits must be absent (not zero-rows).

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
