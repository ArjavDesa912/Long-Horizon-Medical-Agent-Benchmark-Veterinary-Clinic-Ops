# 039_low_stock_supplier_summary — REDTEAM notes

## Mission
Group the reorder problem by supplier for the weekly order call. One ops_reports row per supplier that has at least one item at or below reorder level: {report: 'supplier_reorder', batch_code, supplier, items_below: <count of that supplier's rows with qty <= reorder_level>, est_cost: <sum over those rows of unit_price*(reorder_level*2 - quantity_on_hand), dollars>, locations_affected: <comma-joined sorted distinct location_ids>}. Any order.

## Why this is hard / unique
Group-by over a filtered set with a derived cost formula and a sorted-CSV field; agents botch the CSV ordering.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
