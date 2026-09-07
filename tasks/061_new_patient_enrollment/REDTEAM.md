# 061_new_patient_enrollment — REDTEAM notes (Phase 4 PENDING)

## Mission
Complete the full new-patient intake bundle for Maple Syrup, an exotic rabbit, under the episode batch code: create the patient record, schedule a wellness exam with the correct provider, create a draft estimate, send a welcome communication, and append an audit entry.

## Why this is hard / unique
- Multi-collection bundle: the task touches patients, appointments, billing_estimates, communications, and audit_log.
- Live resolution: the provider must be found by specialty and location, and the estimate price must be read from the fee schedule at runtime.
- Format discipline: the new microchip must be a 15-digit ISO 11784 number, distinct from every existing 11/12-digit chip in the snapshot.
- Constrained scheduling: the appointment must use a specific free slot (09:00–09:30, Exam 2) and match the resolved provider.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Microchip-format decoy**: the snapshot has 300 non-compliant microchips — 299 are 12 digits (e.g., patient 1 '985112100000') and patient 30 has 11 digits ('98511232965'). The new patient must use the explicit 15-digit id 985112900001234.
- **Provider resolution hazard**: only provider id 2 at location 1 lists 'exotics' in specialties (Dr. Marcus Chen). Confirmed from `veterinary_clinic_system_providers`.
- **Existing-patient collision**: owner 3 already owns patient 5 (Clementine), patient 27 (Poppy, status 'transferred'), and patient 248 (Lucy, avian). Verified from `veterinary_clinic_system_patients`.
- **Fee schedule lookup**: the location-1 fee schedule `WELL-EXAM` item is price 62. Confirmed from `veterinary_clinic_system_fee_schedules`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
