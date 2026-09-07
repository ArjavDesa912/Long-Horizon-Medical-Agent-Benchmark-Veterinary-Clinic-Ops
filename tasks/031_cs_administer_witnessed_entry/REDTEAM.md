# 031_cs_administer_witnessed_entry — REDTEAM notes (Phase 4 PENDING)

## Mission
Log a controlled-substance administration end-to-end: resolve the names in the clinical note to live records, append one `controlled_substance_log` row, decrement the matching `pharmacy_inventory` row by 0.2, append an `audit_log` entry, and push an `ops_reports` summary. The entire workflow must be idempotent and leave all seed rows outside the blast radius untouched.

## Why this is hard / unique
- Multi-hop name resolution across `patients`, `providers`, `locations`, and `pharmacy_inventory` instead of hardcoded ids.
- The inventory decrement must be the exact same item at the exact same location as the log row.
- Append-only discipline: existing `controlled_substance_log` and `pharmacy_inventory` rows are immutable.
- Idempotency on re-run: the second run must not duplicate the log, re-decrement inventory, or duplicate the summary.
- Dual-path inventory verification (raw-row vs SQL) for the adjusted quantity.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Name-to-record resolution**: `patients.id=4`, `name='Noodle'`, `location_id='1'`; `locations.id=1`, `name='Main Street Animal Hospital'`; `providers.id=1`, `full_name='Dr. Elena Alvarez'`, `role='veterinarian'`; `providers.id=5`, `full_name='Rosa Delgado'`, `role='vet_tech'`. Hardcoded ids or names from a different build fail.
- **Inventory location decoy**: `pharmacy_inventory` has two `Buprenorphine` rows — `id=35` at `location_id='1'` with `quantity_on_hand=7`, and `id=36` at `location_id='2'` with `quantity_on_hand=7`. Only the location-1 row (matching Noodle's location) is decremented to `6.8`.
- **Medication table decoy**: `medications` contains active `Buprenorphine` rows for other patients (e.g., `patient_id='49'`, `'85'`, `'199'`), but none for `patient_id='4'`. The agent must not use the `medications` table as the source of truth; the clinical note names the patient directly.
- **Idempotency**: `controlled_substance_log` already has an existing row for `patient_id='4'` (`id=9`), but it has no batch code in `notes` and `occurred_at` in the past. A solution that keys on `patient_id=4` alone would incorrectly reuse or skip. The correct key is the `notes` field containing the live `batch_code`.
- **Collection scope**: `controlled_substance_log` has 12 seed rows; the agent must append exactly one new row and not edit the existing rows. `pharmacy_inventory` has 42 rows; only one field on one row changes.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
