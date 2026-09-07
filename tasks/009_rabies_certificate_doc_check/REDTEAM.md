# 009_rabies_certificate_doc_check — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the rabies-certificate document audit for the practice as of the episode date. For every existing rabies-certificate file row, set `doc_status` to `current` or `stale` based on the patient's latest rabies due date. For every current-rabies dog or cat without a certificate, push a placeholder file and send the owner an outbound email. Push an `ops_reports` audit row with counts and a `by_location` breakdown. The flow is idempotent and verified via dual raw-row and SQL paths.

## Why this is hard / unique
- Multi-species scope rule: only canines and felines require rabies certificates, even though other species also have rabies records.
- Two-way reconciliation: existing files are annotated, missing files are synthesized, and both are cross-checked against the live vaccination data and the episode date.
- Real red-herring data: non-rabies file rows and non-required species must survive untouched.
- Dual-path verification for every aggregate number (current, stale, by location, with/without certificate) and strict canary checks outside the blast radius.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Non-required species with current rabies**: the seed snapshot has 127 dogs and cats with a rabies record (103 current, 24 stale as of 2026-09-30), plus 5 avians, 4 equines, and 7 exotics with current rabies. Only canines and felines are in scope.
- **Existing non-rabies files**: the seed `files` collection has exactly 7 non-rabies rows (doc_type radiograph, clinical photo, boarding-consent, anesthesia-consent, referral-letter). An over-broad mutation of all files fails the canary.
- **Multi-pet owner name collision**: the 50-name pet pool means two current-rabies dogs of the same owner can share the same name; verifier matches placeholder and communication rows by `patient_id`, not by name.
- **Date boundary around the episode**: three current-rabies patients (121 due 2026-09-30, 208 due 2026-09-30, 288 due 2026-10-01) sit in the jitter band [2026-09-27, 2026-10-03]. The `current` test must use `>=` versus the episode date; at jitter +3 the count drops by one.
- **Idempotency on re-run**: a second run must not duplicate placeholders, communications, or ops_reports rows and must leave the final state byte-identical.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
