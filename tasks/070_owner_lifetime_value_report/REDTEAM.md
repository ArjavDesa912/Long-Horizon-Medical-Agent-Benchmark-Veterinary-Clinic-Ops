# 070_owner_lifetime_value_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Produce the monthly owner LTV, AR aging, and owners.balance reconciliation reports in `ops_reports`. The task fuses client lifetime value ranking, open-AR aging, and a stale-balance reconciliation into one mission.

## Why this is hard / unique
- The `owners.balance` field is a stale cache that must be ignored; the real open AR is derived only from `billing_invoices`.
- AR aging buckets depend on the live `episode_date`, which jitters per episode, so numbers cannot be hardcoded.
- Draft invoices must be excluded from every invoice-derived metric.
- Every aggregate is verified by two independent paths (Python raw-row filter and SQL GROUP BY) before the written rows are checked.
- Includes owners with zero pets or zero revenue and a reconciliation row that depends on cross-collection balance equality.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `owners.balance` disagrees with invoice-derived open AR for 58 owners; specific rows: owner id=1 Margaret Whitfield (balance 134.00 vs open 523.00), owner id=4 Carlos Mendoza (175.00 vs 0.00), owner id=21 Eugene Kim (-45.00).
- Invoice id=3 (INV-1003, owner 3, status `draft`, total 546.00) must not be counted.
- Only invoices id=1 and id=2 are open; their AR buckets vary with the episode date.
- 55 owners have zero pets (e.g. owner id=23 Jeffrey Robinson, id=27 Kenneth Thompson).
- Top owner is id=35 Carol Perez with lifetime_revenue 1970.00.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
