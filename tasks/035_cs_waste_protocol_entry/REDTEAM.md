# 035_cs_waste_protocol_entry — REDTEAM notes

## Mission
Replicate the Controlled Substances tab's waste workflow: a partially used Ketamine vial, 0.5 units, is being wasted at location 1 by Dr. Chen with Miles Turner witnessing. (1) Append the log row: item_name 'Ketamine', location_id '1', action 'waste', quantity 0.5, witnessed_by 'Miles Turner', performed_by 'Dr. Chen', occurred_at episode timestamp, notes 'Partial vial waste <batch_code>'. (2) Decrement the Ketamine pharmacy_inventory row at location 1 by 0.5 (quantity_on_hand is a float here). No other inventory rows change.

## Why this is hard / unique
Log-and-decrement atomicity across collections; float arithmetic on inventory quantity.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
