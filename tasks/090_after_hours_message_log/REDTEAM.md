# 090_after_hours_message_log — REDTEAM notes (Phase 4 PENDING)

## Mission
The answering service takes a voicemail from owner 7 (Frank Kowalski) after hours and the agent must execute the full after-hours triage protocol: log an inbound voicemail, look up the owner’s patient and that patient’s location, determine the on-call veterinarian for that location, send an outbound page to that DVM, and record a triage report in ops_reports.

## Why this is hard / unique
- Multi-hop join through owners, patients, and providers with no row ids given in the instruction.
- Two distinct communications rows with different foreign keys (patient_id vs provider_id) on a collection whose snapshot schema has neither column.
- On-call DVM must be the veterinarian at the patient’s location, not the first provider or a hardcoded id.
- Idempotent report upsert by batch_code.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- 160 pre-existing communications rows with repeated subjects/bodies; new rows must be matched by derived keys, not text.
- Owner 7 → patient 10 (Willow, equine, location_id "2"); provider 9 (Lucy Tran, groomer) is also at location 2, so a role filter is required to pick provider 3 (Dr. Priya Natarajan).
- Providers 1 and 2 are both veterinarians at location 1; a hardcoded first-veterinarian choice fails for this patient.
- ops_reports does not exist in the snapshot; gold must tolerate a missing table on first read.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
