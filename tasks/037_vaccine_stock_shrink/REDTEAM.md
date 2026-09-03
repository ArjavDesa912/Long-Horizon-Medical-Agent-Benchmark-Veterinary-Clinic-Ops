# 037_vaccine_stock_shrink — REDTEAM notes

## Mission
Stock-shrink adjustment: an audit found every location's vaccine stock (item_name containing 'vaccine', case-sensitive) overcounted. Reduce each such row's quantity_on_hand by ops_meta.shrink_pct PERCENT (round DOWN to whole units), and add field shrink_adjusted='<batch_code>'. Non-vaccine rows must remain byte-identical.

## Why this is hard / unique
Per-episode randomized percentage with floor rounding; substring (not category) selection.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
