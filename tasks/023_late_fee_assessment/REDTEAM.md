# 023_late_fee_assessment — REDTEAM notes

## Mission
Finance is assessing late fees. The percentage for THIS episode is stored in veterinary_clinic_system_ops_meta.late_fee_pct (an integer percent). For every invoice with status 'overdue' (after you apply the re-flagging rule: 'sent' with due_date strictly before the episode date becomes 'overdue') and unpaid balance, add a late fee: append a line item {description: 'Late fee (<pct>% of overdue balance)', quantity: 1, unit_price: <round(pct% * unpaid, 2)>} to that invoice, increase total_amount by the same amount, and increase the owner's balance by the same amount. Apply each invoice's fee once. Paid and draft invoices are never touched.

## Why this is hard / unique
Per-episode randomized fee percentage (memorized constants fail), nested line-item append (not replace), and fan-out to owner balances.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
