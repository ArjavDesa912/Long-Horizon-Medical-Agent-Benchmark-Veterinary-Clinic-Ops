# 032_cs_running_balance_reconciliation — REDTEAM notes

## Mission
DEA-style reconciliation: for each controlled item, the expected on-hand balance is sum(receive) - sum(administer) - sum(waste) - sum(dispense) over controlled_substance_log. Compare with pharmacy_inventory.quantity_on_hand for is_controlled items (sum across locations). Create one ops_reports row per controlled item present in the LOG: {report: 'cs_reconciliation', batch_code, item_name, log_balance: <number>, inventory_on_hand: <number or null if no inventory row>, discrepancy: <log_balance - inventory_on_hand, or null>}. Any order. Exactly one row per distinct logged item.

## Why this is hard / unique
Sign-correct multi-action ledger aggregation (receive positive, others negative) and intentional null handling; agents flip dispense/waste signs.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
