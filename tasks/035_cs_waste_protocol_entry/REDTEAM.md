# 035_cs_waste_protocol_entry — REDTEAM notes (Phase 4 PENDING)

## Mission
Run a per-episode parameterized controlled-substance waste event: derive the
target item/location/quantity from ops_meta (`cs_waste_loc_idx`,
`cs_waste_drug_idx`, `cs_waste_qty_tenths`), append a `controlled_substance_log`
waste row with a valid vet+vet-tech pair at that location, decrement the
selected `pharmacy_inventory` row (float math), append an `audit_log`
`CS_WASTE_LOGGED` row pointing at the new log row, and push one `ops_reports`
`waste_protocol` row reconciled against live post-mutation state.

## Why this is hard / unique
- Nonce-parameterized event: the drug, location, and quantity all come from
  ops_meta integer fields — a memorized v1 answer ("Ketamine, loc 1, 0.5")
  is wrong on most episodes.
- Four-collection atomicity with a foreign-key ripple: the audit row's
  `target_id` and the report row's `log_id` must equal the id of the log row
  created in the same run.
- Float-exact decrement (`tenths/10.0`) on integer seeded quantities, plus
  dual-path REST-vs-SQL assertion on the post-decrement value.
- Provider role/location validation forces a real `providers` lookup.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `controlled_substance_log` already contains waste rows that must not be
  edited: id 3 (`waste`, Ketamine, loc 1, 0.4) and id 11 (`waste`, Tramadol,
  loc 2, 0.5, patient_id '10'). Verified in snapshot.
- Every controlled drug exists at both locations 1 and 2: Buprenorphine
  inventory ids 35/36, Tramadol 37/38, Ketamine 39/40, Alprazolam 41/42 —
  item_name-only matching decrements the wrong row or two rows. Verified.
- Seeded log rows carry garbage/empty `witnessed_by` values (ids 2, 4, 5, 8,
  10, 11 show '' or a mojibake character) — copying a witness from an existing
  row fails the vet-tech role/location check. Verified.
- Controlled `quantity_on_hand` is integer-seeded (Ketamine 3) but the waste
  quantity is fractional (e.g. 0.5) — integer math or percent misuse fails the
  1e-9 tolerance check. Verified field types in snapshot.
- `ops_reports` is absent from the snapshot entirely (24 seeded collections,
  no ops_reports) — the table must be created by the first push.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.
