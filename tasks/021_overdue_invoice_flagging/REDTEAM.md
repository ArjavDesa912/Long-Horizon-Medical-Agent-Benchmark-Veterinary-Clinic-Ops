# 021_overdue_invoice_flagging — REDTEAM notes

## Mission
Month-end housekeeping: in billing_invoices, every invoice with status 'sent' whose due_date is strictly before the episode date (ops_meta.episode_date) must be re-flagged status='overdue'. Invoices already paid, drafts, or not yet due stay exactly as they are. Nothing else changes.

## Why this is hard / unique
Single-collection conditional status migration; the trap is touching 'sent' invoices whose due date is in the future.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
