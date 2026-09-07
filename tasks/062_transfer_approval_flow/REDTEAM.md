# 062_transfer_approval_flow — REDTEAM notes (Phase 4 PENDING)

## Mission
Process the pending location transfer queue, completing routine transfers while leaving specialist-hold and already-approved requests untouched. Move the patients' locations, append audit rows, produce a transfer_sweep ops_report, and send a communications summary.

## Why this is hard / unique
- Multi-state text filter: the decision depends on both `status='pending'` and a case-insensitive check for the word 'specialist' in the note.
- Audit/report/communication bundle: the same queue sweep produces three different artifacts in different collections.
- Dual-path verification: `completed_now` is recomputed both from the live-vs-snapshot completed count and from the new audit_log rows for the batch.
- Idempotency: a second run must not create duplicate audit, communication, or ops_report rows.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Specialist-hold decoy**: `location_transfers` id 7 is `status='pending'` with note 'Specialist follow-up at Riverside' and patient 30. Confirmed from `veterinary_clinic_system_location_transfers`.
- **Approved-transfer decoy**: `location_transfers` id 4 is `status='approved'` with empty note and patient 19 (patient 19 currently has `location_id` '2', matching the `to_location_id`). Confirmed from snapshot.
- **Pre-existing completed transfers**: ids 3, 5, and 6 are already completed. The audit_log seed contains one `TRANSFER_COMPLETED` row for patient 15 (id 3). These must not be altered or duplicated.
- **Patient-location consistency**: for the two target transfers (ids 1 patient 3 -> loc 2, and id 2 patient 10 -> loc 3), the patient `location_id` must equal the transfer's `to_location_id`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
