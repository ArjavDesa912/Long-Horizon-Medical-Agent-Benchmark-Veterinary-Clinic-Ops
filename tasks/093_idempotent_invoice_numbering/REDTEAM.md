# 093_idempotent_invoice_numbering — REDTEAM notes

## Mission
Every invoice must have a canonical public_ref derived deterministically: 'PUB-<invoice_number>'. Set public_ref on every invoice that lacks it or has a wrong value. Rows already correct must remain byte-identical (do NOT rewrite updated_at by no-op updates). Then create exactly one ops_reports row {report: 'public_ref_backfill', batch_code, backfilled: <count of rows you changed>, total: <invoice count>} — but if a report row with this episode's batch_code already exists for report 'public_ref_backfill', update it instead of inserting a second one.

## Why this is hard / unique
Idempotent upsert of BOTH data and its own report row; no-op update detection via byte-identity (updated_at drift fails).

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
