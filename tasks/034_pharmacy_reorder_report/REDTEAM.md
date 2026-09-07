# 034_pharmacy_reorder_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the weekly pharmacy reorder and controlled-substance review. For every `pharmacy_inventory` row at or below its reorder level, push an item-level `ops_reports` row with supplier, price, suggested order, projected cost, active prescription count, and (for controlled items) a per-location log-balance/discrepancy. Push a summary row and an `audit_log` entry.

## Why this is hard / unique
- Multi-collection join: inventory, controlled-substance log, locations, and medications.
- Multi-location duplicate keys (e.g., Bordetella at both locations) require (item, location) as the report key.
- At-or-below reorder boundary and `suggested_order = reorder_level*2 - quantity_on_hand` (not just reorder_level - quantity).
- Controlled-substance reconciliation is mixed into a purchasing report, with null log_balance/discrepancy for non-controlled items.
- Active-prescription count adds a second derived fact per row.
- Dual-path verification of every aggregate and every row.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Multi-location duplicate keys**: `Bordetella vaccine`, `Convenia injection`, and `Microchip scanner battery` each appear at `location_id='1'` and `'2'`. Reporting by `item_name` alone would merge or drop one of each pair.
- **At-or-below boundary**: `Convenia injection` at both locations has `quantity_on_hand=4` and `reorder_level=4`, so it qualifies. The `suggested_order` is `4`, not `0`.
- **Suggested-order formula**: the correct formula is `reorder_level * 2 - quantity_on_hand`. For `Bordetella vaccine` (qty 9, reorder 10) this is `11`; for `Microchip scanner battery` (qty 3, reorder 4) this is `5`; for `Ketamine` (qty 3, reorder 4) this is `5`.
- **Controlled filter and per-location log balance**: only `Ketamine` is both qualifying and controlled. Its log balance is `location_id='1': -2.9` (discrepancy `-5.9`) and `location_id='2': -5.0` (discrepancy `-8.0`). `Buprenorphine`, `Tramadol`, and `Alprazolam` are controlled but not below reorder, so they are excluded.
- **Active prescriptions**: `medications` has 9 active `Ketamine` rows and 0 for the other qualifying item names (`Bordetella vaccine`, `Convenia injection`, `Microchip scanner battery`).
- **Projected-cost precision**: the total projected cost is `$1,626.50` (cents `162650`). Each row's cost is `suggested_order * unit_price`, compared in cents.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
