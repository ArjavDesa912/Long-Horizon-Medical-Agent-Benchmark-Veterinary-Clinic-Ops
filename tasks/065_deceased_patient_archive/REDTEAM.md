# 065_deceased_patient_archive - REDTEAM notes (Phase 4 PENDING)

## Mission
A client reports a pet's death, but the patient must be derived from live data: the active patient with the earliest future scheduled/confirmed appointment among those that also have a future reserved boarding stay. Archive that patient (status 'deceased', archived batch), cancel future boarding and appointments, archive (not delete) waiting waitlist entries, notify the owner, and write ops_reports and audit_log rows.

## Why this is hard / unique
- The target is not a fixed id; it changes with the episode date and the seed data.
- Cross-collection cascade touches 7 collections with 4 different mutation semantics (update/cancel/archive/delete-pending).
- Dual-path verification (Python filter vs SQL) on the derived target and every cancellation count.
- Idempotent re-run: the same batch code, target, and counts must be reproduced exactly.

## Hazards planted (task.json.hazards) - confirmed against seed_snapshot.json
- Patient 17 (Rocket) is now active and no longer the target (id 17, status 'active', owner 13).
- Episode-date dependent targets: patient 1 (owner 1) for 2026-09-27/28, patient 200 (owner 211) for 2026-09-29, patient 204 (owner 36) for 2026-09-30/01/02/03 (appointment 418, reservation 81).
- 7 reserved boarding reservations have check_in before the episode date (ids 6, 7, 8, 17, 65, 85, 98 with check_in on 2026-09-24 or earlier).
- Appointments have many non-future/non-scheduled statuses (176 completed, 66 no_show, 10 checked_in).
- Waitlist has 6 rows for patients 3, 7, 11, 15, 19, 23.

## Phase 4 - NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
