# 079_appointment_to_visit_linkage — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the appointment-to-visit follow-through audit: every completed appointment must have a matching visit_records row by exact triple (patient_id, provider_id, calendar-day visit_date). Create the missing visit records, set generated_from to the source appointment id, and write one follow_through ops_reports row with the counts and id lists.

## Why this is hard / unique
- **Reconciliation first**: the agent must discover the one completed appointment that already has a matching seed visit record and not duplicate it.
- **Exact triple match**: patient_id + provider_id + date; partial matches over-match and fail the count.
- **Duplicate triples**: two pairs of completed appointments share the same triple, so one-visit-per-triple produces the wrong count and generated_ids set.
- **Generated source tracking**: each new visit row must carry generated_from and a subjective note pointing back to the appointment id so the verifier can check identity and catch shortcut reports.
- **Dual-path verification**: counts are recomputed from raw rows and from independent SQL joins / id-threshold queries.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Pre-existing match**. Snapshot `veterinary_clinic_system_appointments` id 486 has `{patient_id: 30, provider_id: 3, appointment_date: 2026-08-29T00:00:00+00:00, status: completed}`. Snapshot `veterinary_clinic_system_visit_records` id 164 has `{patient_id: 30, provider_id: 3, visit_date: 2026-08-29T00:00:00+00:00}`. This is the only completed appointment whose triple matches a seed visit.
2. **Duplicate completed triples**. Appointment ids 150 and 378 both have `(patient_id 67, provider_id 3, appointment_date 2026-08-19)`. Appointment ids 154 and 155 both have `(patient_id 61, provider_id 3, appointment_date 2026-08-05)`. With 176 total completed appointments, the correct number of new visit records is 175.
3. **Decoy seed visits**. `veterinary_clinic_system_visit_records` has 371 seed rows (ids 1..371) and `generated_from` is `None` on every seed row; 370 of them have no matching completed appointment and must remain byte-identical.
4. **Partial-match traps**. There are 176 completed appointments and 371 seed visit records. Matching only on `patient_id` or only on `visit_date` would produce many false matches and the wrong generated count.
5. **No-visit 100% report**. An agent could write `ops_reports` with `match_pct=100.0`, `unmatched_ids=""`, and `generated_ids` filled in without creating the visit records. The verifier counts actual new `visit_records` rows and checks the `generated_from` set identity, so the shortcut fails.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
