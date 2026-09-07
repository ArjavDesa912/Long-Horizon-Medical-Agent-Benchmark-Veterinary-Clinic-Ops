# 032_cs_running_balance_reconciliation — REDTEAM notes (Phase 4 PENDING)

## Mission
Reconcile controlled-substance logs with physical inventory on a per-item, per-location basis. For every `pharmacy_inventory` row where `is_controlled` is true, compute the expected log balance from `controlled_substance_log` entries at the same location, compare it to `quantity_on_hand`, and push one `ops_reports` row plus a summary `audit_log` entry.

## Why this is hard / unique
- Per-location reconciliation rather than simple item-level aggregation — the log and inventory are both location-specific.
- Some controlled inventory rows have no matching log activity at that location (Alprazolam at location 1, Buprenorphine at location 1), requiring the agent to report a log_balance of 0.0.
- Sign discipline: `receive` adds; `administer`, `waste`, and `dispense` all subtract.
- The report must include only controlled inventory rows, not every item in `pharmacy_inventory`.
- Dual-path verification: Python aggregation and SQL JOIN/GROUP BY must agree on every number.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Location-conflation trap**: `controlled_substance_log` has Buprenorphine activity only at `location_id='2'` (rows 1, 5, 9), but `pharmacy_inventory` has Buprenorphine at both `location_id='1'` and `'2'`. Summing across locations gives a log_balance of 9.5 vs. 7 for both locations, which is wrong for each.
- **Missing-log-location trap**: `pharmacy_inventory` rows for `Alprazolam` at `location_id='1'` (`id=37`, `quantity_on_hand=11`) and `Buprenorphine` at `location_id='1'` (`id=35`, `quantity_on_hand=7`) have no corresponding `controlled_substance_log` entries. A solution that only reports items present in the log will omit these and miss their negative discrepancies (`-11` and `-7`).
- **Sign trap**: The log contains `receive` (adds), `administer`, `waste`, and `dispense` (all subtract). For example, Ketamine at `location_id='1'` has two subtract actions (`administer` 2.5 and `dispense` 5.0) and no receive, giving `log_balance=-2.9`.
- **Controlled filter**: Of 42 `pharmacy_inventory` rows, only 8 are controlled: `Buprenorphine`, `Tramadol`, `Ketamine`, and `Alprazolam`, each at locations 1 and 2. Non-controlled items such as `Bordetella vaccine` and `Microchip scanner battery` must not appear in the report.
- **Witnessed-by decoy**: `controlled_substance_log.id=11` (Tramadol waste at location 2) has an empty `witnessed_by`, but this is a reconciliation task, not a correction task. Any mutation of the log fails the canary check.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
