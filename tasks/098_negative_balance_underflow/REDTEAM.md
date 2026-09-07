# 098_negative_balance_underflow — REDTEAM notes (Phase 4 PENDING)

## Mission
Repair client accounts whose owner balance has underflowed below zero by moving the negative amount into a positive `credit_balance`, zeroing `balance`, tagging the owner with the episode batch code, appending a `CREDIT_BALANCE_FIX` audit entry, and writing a summary `ops_reports` row. Non-negative owners and all collections outside `owners`, `audit_log`, and `ops_reports` must remain byte-identical.

## Why this is hard / unique
- **Rare-event repair**: only one of 220 owners is negative, forcing the agent to derive the scope from live data rather than a rule of thumb.
- **Cents-exact financial mutation**: the credit must be the positive cent equivalent of the negative balance; sign-flip and rounding are both failure modes.
- **Multi-collection audit trail**: the repair must produce both an `audit_log` and an `ops_reports` row, and both must self-consistently reference the owner.
- **Dual-path verification**: every aggregate (owner count, total credit, audit count) is recomputed from SQL and from the API and must agree.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Owner id=21 (`Eugene Kim`) is the only owner with `balance < 0` (`-45.0`); owners id=2, 3, 6, 7, and 8 are confirmed `balance == 0.0`.
- No `billing_invoice` has `amount_paid > total_amount`; the 257 `paid` invoices are paid exactly.
- The snapshot has no `credit_balance` or `credit_fixed` fields on `owners`; they are created by the repair.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
