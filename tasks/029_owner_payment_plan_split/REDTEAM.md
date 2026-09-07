# 029_owner_payment_plan_split — REDTEAM notes (Phase 4 PENDING)

## Mission
Identify the largest open unpaid invoice, split it into two equal sent installments, send a payment-plan communication to the owner, and write a `payment_plan` ops_reports row. The owner balance stays unchanged.

## Why this is hard / unique
- Multi-hop selection: the target is the max of `(total_amount - amount_paid)` over open invoices, not simply the max `total_amount`.
- Cent-conserving split arithmetic: floor/remainder with A+B equal to the original unpaid amount exactly.
- Fuses create (new invoices, communication, report) and aggregation (target selection) into one workflow.
- Dual-path verification of the target invoice and split amounts via Python and SQL.
- Idempotent re-run: detects existing split invoices and the report and does not create a second plan.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Paid decoys**: 257 `paid` invoices have large `total_amount` values (e.g., INV-1008 at $668.00) but `amount_paid == total_amount`, so their unpaid is 0. A solution that selects by `total_amount` alone will pick a paid invoice and create a plan for an already-paid bill.
- **Draft decoy**: `INV-1003` is `draft` with $546.00 unpaid, larger than the largest open invoice. The target filter must exclude `draft` invoices. A solution that selects the largest `total_amount - amount_paid` across all statuses picks INV-1003.
- **Open invoices**: Only `INV-1001` (sent, $523.00 unpaid, due 2026-08-21, owner 1, patient 1, location 1) and `INV-1002` (sent, $214.00 unpaid, due 2026-09-20, owner 2, patient 3) are eligible. Both are past due at all allowed episode dates, so the target is `INV-1001` by amount. If they were tied, the lower invoice number (`1001`) would win.
- **Cent conservation**: $523.00 = 52,300 cents. `half_a = 52300 // 2 = 26150` cents ($261.50); `half_b = 52300 - 26150 = 26150` cents. A+B = 52300 cents exactly. A solution that splits 523/2 = 261.5 and rounds both to 261.5 is fine, but an odd-cent total would expose a rounding error.
- **Due dates**: Split A is due episode + 14 days; split B is due episode + 28 days. For episode 2026-09-30, due dates are 2026-10-14 and 2026-10-28. The original invoice `due_date` must not be reused.
- **Owner balance**: Owner 1's balance is $134.00 in the seed. The task explicitly says the owner balance stays as it was; updating it to the new AR fails.
- **Re-run hazard**: After the first run the original is `split` and two new `sent` invoices exist with future due dates. A naive re-run would select `INV-1002` (now the largest open invoice) and create a second plan. The gold checks for an existing `payment_plan` report and returns if found.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
