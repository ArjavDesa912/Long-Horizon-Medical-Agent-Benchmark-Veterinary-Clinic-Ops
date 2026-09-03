# 086_owner_statement_messages — REDTEAM notes

## Mission
Monthly statements: for every owner whose current balance is greater than 0, push one communications row {channel: 'email', direction: 'outbound', subject: 'Statement ready — balance $<balance with 2 decimals>', body: 'Your statement for <N> open invoice(s) is ready. Balance $<balance>.', logged_by: 'system', occurred_at: episode timestamp} where N is that owner's count of invoices with status 'sent' or 'overdue' (N may be 0). Owners with zero balance get nothing.

## Why this is hard / unique
Money formatting embedded in two template spots + zero-balance exclusion + a possibly-zero invoice count.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
