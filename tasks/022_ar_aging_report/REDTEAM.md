# 022_ar_aging_report — REDTEAM notes

## Mission
Build the standard accounts-receivable aging summary (the 0–30 / 31–60 / 61–90 / 90+ day buckets every practice manager runs — verify the bucket convention online if needed). Consider only invoices with status 'sent' or 'overdue' and unpaid balance (total_amount - amount_paid > 0); age is measured from issued_date to the episode date. Create one ops_reports row: {report: 'ar_aging', batch_code, bucket_0_30: <total unpaid aged 0..30 days, dollars>, bucket_31_60, bucket_61_90, bucket_90_plus, invoice_count: <invoices considered>}. Money fields are numbers in dollars.

## Why this is hard / unique
Domain bucket convention (boundary 30/60/90) + partial-payment netting (total minus paid); agents usually age from due_date instead of issued_date.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
