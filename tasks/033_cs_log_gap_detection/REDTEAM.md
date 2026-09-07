# 033_cs_log_gap_detection — REDTEAM notes (Phase 4 PENDING)

## Mission
Audit the controlled-substance log for witness-compliance gaps. Only `administer` and `waste` rows with an empty or em-dash `witnessed_by` are corrected, and the correction must use a veterinarian or vet_tech at the same location. Produce an `ops_reports` summary and one `audit_log` row per fix.

## Why this is hard / unique
- Rule-conditioned repair: the set of rows to fix is defined by action, witness value, and provider location/role, not by a hardcoded list.
- Em-dash placeholders on `receive` and `dispense` rows are legitimate and must survive unchanged.
- The witness is location-specific (first veterinarian at that location by provider id), so a universal `Dr. Alvarez` hardcode fails.
- Dual-path verification of the violation set and the assigned witness (Python vs SQL).
- Multi-hop summary: the `ops_reports` corrections list includes resolved `patient_name`.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Single real violation**: `controlled_substance_log.id=11` is `Tramadol` `waste` at `location_id='2'`, `performed_by='Josie Baker'`, `patient_id='10'`, `witnessed_by=''`. It is the only row that satisfies both `action IN ('administer','waste')` and an empty/em-dash `witnessed_by`.
- **Em-dash decoy rows**: `controlled_substance_log` rows 2, 4, 5, 8, 10 have `witnessed_by='\u2014'` (em dash) but `action` is `dispense` or `receive`. These are not violations and must not be modified.
- **Location-specific witness**: the violation is at `location_id='2'`. The providers at location 2 are `Dr. Priya Natarajan` (id 3, veterinarian), `Miles Turner` (id 6, vet_tech), and `Lucy Tran` (id 9, groomer). The first veterinarian is `Dr. Priya Natarajan`, so that must be the assigned witness.
- **Role validation**: `Lucy Tran` is a `groomer` and `Josie Baker` is a `kennel_attendant`. Neither role is a valid witness; only `veterinarian` or `vet_tech` are accepted.
- **Patient name resolution**: the corrected row has `patient_id='10'`, which is `patients.id=10`, `name='Willow'`. The `ops_reports` corrections list must include this name, not just the id.
- **Idempotency**: after the first run, `controlled_substance_log.id=11` has `witnessed_by='Dr. Priya Natarajan'` and `witness_corrected=<batch>`. A second run must not re-update it and must not produce duplicate `audit_log` or `ops_reports` rows.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
