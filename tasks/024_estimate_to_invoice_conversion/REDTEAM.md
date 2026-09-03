# 024_estimate_to_invoice_conversion — REDTEAM notes

## Mission
Do what the Billing → Estimates screen's 'Convert to invoice' action does for every estimate with status 'accepted': create a new invoice with invoice_number 'INV-C<batch_code>-<estimate_number digits>' (e.g. EST-3005 -> digits 3005), owner/patient/location copied from the estimate, issued_date = episode date, due_date = episode date + 21 days, line_items copied from the estimate, total_amount = estimate total, amount_paid = 0, status 'sent'; then set the estimate's status to 'converted'; then append one audit_log row per conversion {actor: 'Dana Whitaker', actor_role: 'org_admin', action: 'ESTIMATE_CONVERTED', target_collection: 'billing_estimates', target_id: <estimate id as string>, details: 'Converted to invoice INV-C<batch_code>-<digits>', occurred_at: episode timestamp}. Estimates with any other status stay untouched.

## Why this is hard / unique
Three-collection transaction with audit trail and nonce-derived numbering; skipping the audit entry is the common shortcut that fails.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
