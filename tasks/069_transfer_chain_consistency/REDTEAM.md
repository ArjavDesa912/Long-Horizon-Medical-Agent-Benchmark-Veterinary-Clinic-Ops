# 069_transfer_chain_consistency - REDTEAM notes (Phase 4 PENDING)

## Mission
Reconcile location transfer chains: for each patient with completed transfers, mark earlier completed transfers as 'superseded' when their to_location_id does not match the patient's current location. Do not modify patients or non-completed transfers. Produce per-patient and summary ops_reports, owner communications for each superseded transfer, and an audit log.

## Why this is hard / unique
- Temporal chain reasoning: latest completed transfer by requested_at is the authority, with id as tie-breaker.
- Only completed transfer rows change; patients, pending, and approved transfers are hazards.
- Cross-collection verification (transfers, patients, ops_reports, communications, audit_log).
- Dual-path superseded set: Python sort vs SQL correlated subquery.
- Idempotent re-run across four write collections.

## Hazards planted (task.json.hazards) - confirmed against seed_snapshot.json
- Patient 26 has completed transfers id 5 (to 1, 2026-06-06) and id 6 (to 3, 2026-08-20); current location 3, so id 5 must be superseded.
- Patient 15 has one completed transfer id 3 (to 3, 2026-08-05) and current location 3; no supersede.
- Patients 3, 10, 30 have pending transfers to locations different from current location; patient 19 has an approved transfer to 2 and current location 2.
- Only 7 transfer rows exist; the superseded set is small but easy to overfit.

## Phase 4 - NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
