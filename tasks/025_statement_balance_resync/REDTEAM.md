# 025_statement_balance_resync — REDTEAM notes

## Mission
An auditor found that owner balances have drifted from the invoice ledger. The correct balance for each owner is the sum of (total_amount - amount_paid) over that owner's invoices with status 'sent' or 'overdue' — paid and draft invoices don't count. Set every owner's balance to exactly that computed amount (which may be 0), then add balance_resynced='<batch_code>' to every owner row whose balance you changed. Do not create or delete owners, and change no other fields. Do not modify billing_invoices.

## Why this is hard / unique
Derived-value repair where the correct answer is a computed aggregate, and only-drifted-rows-get-tagged is a second derivable assertion; blanket-tagging fails.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
