# 036_inventory_valuation_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Month-end inventory valuation: one `ops_reports` `inventory_valuation` row per
location that has `pharmacy_inventory` rows (with `location_name` resolved via
the locations collection), one `inventory_valuation_rollup` `ALL` row that must
internally equal the sum of the parts, and one `audit_log`
`INVENTORY_VALUATION` row — all seven aggregates (item_count, medication_value,
supply_value, controlled_units, controlled_value, low_stock_count,
reorder_cost) derived from live inventory.

## Why this is hard / unique
- Dual-path verification on every aggregate: raw-row Python vs SQL GROUP BY
  with CASE-conditional sums must agree with each other AND the written rows.
- Controlled items are deliberately double-counted (category 'medication' AND
  is_controlled) — the most natural wrong solution under-reports
  medication_value.
- The rollup row adds an internal-consistency dimension: it must equal the sum
  of the agent's own per-location rows, not just the independent computation.
- `pharmacy_inventory` is read-only in this mission but canaried, so any
  "fix the data to match my report" attempt fails.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Controlled inventory rows 35-42 (Buprenorphine/Tramadol/Ketamine/Alprazolam
  at locs 1+2) carry category='medication' AND is_controlled=true AND
  dea_schedule — verified in the snapshot; each is $55.0 x qty.
- All 42 inventory rows have location_id '1' or '2'; location '3' (Cedar Park
  Animal Care Center, in the locations seed) has none — a per-location loop
  over `locations` emits a bogus third row. Verified.
- Inclusive low-stock boundary: Convenia ids 17/18 (4 <= 4), battery ids
  29/30 (3 <= 4), Ketamine ids 39/40 (3 <= 4), Bordetella ids 7/8 (9 <= 10)
  — 4 low-stock rows per location, reorder_cost 813.25. Verified.
- `audit_log` seed has 4 rows including id 3 `CS_LOG_APPENDED` — a
  controlled-substance-looking decoy that must not be edited. Verified.
- `ops_reports` is absent from the 24-collection snapshot — must be created
  by the agent's first push.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.
