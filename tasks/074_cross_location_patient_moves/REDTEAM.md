# 074_cross_location_patient_moves — REDTEAM notes (Phase 4 PENDING)

## Mission
Audit inter-location patient transfers: a transfer matrix, a reconciliation of completed/pending transfers against the patient registry and audit log, and a pending-transfer review list.

## Why this is hard / unique
- The transfer log must be reconciled with `patients.location_id`, `audit_log` (for `TRANSFER_COMPLETED` entries), and `appointments` (for destination conflicts).
- Completed transfers can be stale; the most active lane has a deterministic alphabetical tiebreak.
- Pending transfers may have the patient no longer at the source or already scheduled at the destination.
- A single patient can have multiple transfer rows, requiring duplicate-patient counting rather than row counting.
- Dual-path verification on the matrix and every reconciliation count.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Transfer matrix: lanes '1->2' and '1->3' both have 2 rows; most_active_lane must be '1->2' (alphabetical tiebreak).
- Completed transfer id=5 (patient 26, from 2 to 1) is stale because patient 26's current location is 3 (superseded by transfer id=6 to 3).
- `audit_log` has only one `TRANSFER_COMPLETED` row for `patients` target_id '15' (transfer id=3); completed transfers id=5 and id=6 (patient 26) have no audit row.
- Pending transfer id=7 (patient 30, from 1 to 2) has patient current location 3 (not at source) and 2 appointments at destination 2.
- Patient 26 has two transfer rows (id=5, id=6); all others have one, so duplicate_patient_count is 1.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
