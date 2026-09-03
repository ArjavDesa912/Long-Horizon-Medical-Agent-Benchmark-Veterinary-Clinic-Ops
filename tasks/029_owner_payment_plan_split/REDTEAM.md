# 029_owner_payment_plan_split — REDTEAM notes

## Mission
The owner with the single largest unpaid overdue invoice asks to split it into two equal payments. Find that invoice (status 'overdue' or 'sent' past due; if tied on amount, pick the lower invoice number). Then: (1) mark the original invoice status 'split' and add field split_into='<batch_code>-A,<batch_code>-B'; (2) create two new invoices numbered 'INV-S<batch_code>-A' and 'INV-S<batch_code>-B', each with the same owner/patient/location as the original, line_items=[{description: 'Payment plan part A of INV-<original number>' (or part B), quantity: 1, unit_price: <half the original unpaid balance — round A DOWN to whole cents and give B the remainder so A+B equals the original exactly>}], total_amount equal to that part's unit_price, amount_paid 0, status 'sent', issued_date = episode date, due_date = episode date + 14 days for A and + 28 days for B. The owner's balance stays exactly as it was.

## Why this is hard / unique
Rounding-down/remainder split arithmetic with exact cent conservation, nonce-derived numbering, and a no-net-balance-change invariant.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
