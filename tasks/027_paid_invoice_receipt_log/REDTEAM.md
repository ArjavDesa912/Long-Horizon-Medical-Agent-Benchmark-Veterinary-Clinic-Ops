# 027_paid_invoice_receipt_log — REDTEAM notes

## Mission
The front desk must log a receipt confirmation for every invoice that was paid this calendar month of the episode date. For each invoice with status 'paid' whose issued_date falls in the same calendar month as the episode date, push one communications row to that invoice's owner: channel='email', direction='outbound', subject='Payment receipt INV-<number>', body='Thank you — INV-<number> paid in full ($<total with 2 decimals>).', logged_by='Front desk (Main St)', occurred_at on the episode date. One row per invoice. Seeded communications stay untouched.

## Why this is hard / unique
Calendar-month window (not rolling 30 days) + exact money formatting in a string; both are frequent agent errors.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
