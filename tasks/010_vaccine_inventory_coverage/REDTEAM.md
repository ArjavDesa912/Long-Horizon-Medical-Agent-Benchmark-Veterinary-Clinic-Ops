# 010_vaccine_inventory_coverage — REDTEAM notes

## Mission
Does the pharmacy hold enough vaccine to cover everything coming due? Create veterinary_clinic_system_ops_reports rows (report='vaccine_coverage', batch_code from ops_meta) — one per mapping below, with fields {vaccine_type, item_name, due_next_30: <vaccination rows of that type with due_date in [episode_date, episode_date+30]>, on_hand: <TOTAL quantity_on_hand across all pharmacy_inventory rows whose item_name starts with the mapped product prefix>, coverage_gap: max(0, due_next_30 - on_hand)}. Mappings: rabies→'Rabies vaccine 1yr', DHPP→'DHPP vaccine', FVRCP→'FVRCP vaccine', bordetella→'Bordetella vaccine'. Exactly 4 rows, any order, no extras.

## Why this is hard / unique
Cross-collection join between clinical demand and inventory supply with prefix matching (item names don't equal vaccine types); inclusive-window boundary errors are the classic failure.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
