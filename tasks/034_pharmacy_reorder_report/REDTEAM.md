# 034_pharmacy_reorder_report — REDTEAM notes

## Mission
Purchasing wants the reorder list. Create one ops_reports row per pharmacy inventory item whose quantity_on_hand is at or below its reorder_level: {report: 'reorder_list', batch_code, item_name, location_id, quantity_on_hand, reorder_level, suggested_order: <reorder_level*2 - quantity_on_hand>}. Any order; exactly the qualifying items, no others.

## Why this is hard / unique
At-or-below boundary (<=) and a computed order quantity; off-by-one on the boundary is the classic miss.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
