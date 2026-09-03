# 028_draft_invoice_purge — REDTEAM notes

## Mission
Delete every billing invoice with status 'draft'. Paid, sent, and overdue invoices must remain exactly as seeded. Report nothing; just leave the ledger clean.

## Why this is hard / unique
Surgical delete with exact preservation of survivors — bulk-delete-then-reinsert hacks fail byte-identity (ids/updated_at).

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
