# 086_owner_statement_messages — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the monthly owner statement cycle: for every owner with a positive current balance, push an email statement with exact 2-decimal money formatting in both the subject and body, using the live open-invoice count (sent/overdue). Then create an ops_reports `owner_statements` row with batch_code, counts, totals, and a by_owner JSON.

## Why this is hard / unique
- Money formatting is embedded in two template spots and must be exactly two decimals.
- The open-invoice count can be zero for the majority of positive-balance owners (55 of 56 in the snapshot).
- The `owners.balance` field is the statement amount, which can differ from the sum of open invoice totals (owner 1: balance 134.0 vs open total 523.0).
- Dual-path SQL vs raw-row verification on open counts and open totals.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `owners` id=2 has `balance` 0.0 but `billing_invoices` id=2 (owner_id=2, status='sent', total 214, amount_paid 0). They must not receive a statement.
- `owners` id=1 has `balance` 134.0 while `billing_invoices` id=1 (owner_id=1, status='sent', total 523, amount_paid 0). The statement must show balance 134.00, not 523.00.
- `billing_invoices` id=3 (owner_id=3, status='draft', total 546) is a draft and must not be counted as open.
- 56 owners have positive balance but 55 have zero open invoices, e.g., owner id=4 balance 175.0, id=5 balance 412.5, id=10 balance 128.0. Body must say "0 open invoice(s)".
- Money formatting must be two decimals: e.g., owner id=5 balance 412.5 renders as $412.50; id=15 balance 55.0 renders as $55.00.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
