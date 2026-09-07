# 005_vaccine_lot_recall_trace — REDTEAM notes

## Mission
A manufacturer recalled one vaccine lot: the lot_number that appears most frequently across all vaccination records, breaking ties by choosing the alphabetically smallest lot_number. Find every patient who received that lot, and for each affected patient push one phone/outbound communications row to the owner and one recall_callback reminder_queue row. Then write one ops_reports summary with counts and inventory on_hand, plus one audit_log entry.

## Why this is hard / unique
- Mode-with-tiebreak aggregation over `vaccinations`.
- Distinct patient fan-out through `patients` / `owners`.
- Inventory coverage gap requires joining `pharmacy_inventory` by vaccine type.
- All aggregates (mode, total, affected patients/owners, on_hand) are verified by dual Python/SQL paths.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Three-way tie at frequency 2** — lots `BO-6987-A`, `FV-1313-C`, `FV-1412-A` each appear twice; all other lots appear once. Alphabetical tiebreak selects `BO-6987-A`.
2. **Decoy non-modal lots** — `FV-1313-C` and `FV-1412-A` must not be recalled.
3. **Distinct patient, not distinct owner** — one owner may have multiple pets; exactly one communication and one reminder per affected `patient_id`.
4. **Recalled vaccine_type derived from data** — `BO-6987-A` is `bordetella`; inventory lookup must use that type, not a hardcoded name.
5. **Single combined report** — `ops_reports` must hold exactly one row with `report='lot_recall_trace'` and the live `batch_code`, containing all six aggregate fields.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships.
