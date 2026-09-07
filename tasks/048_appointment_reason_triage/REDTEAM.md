# 048_appointment_reason_triage — REDTEAM notes (Phase 4 PENDING)

## Mission
Triage-tag future scheduled/confirmed appointments and all waiting waitlist rows by reason-based keyword rules, set waitlist slot_status based on whether the patient has a real future appointment, and write a triage_summary ops_reports row.

## Why this is hard / unique
- **Decoy priority field**: the waitlist already contains a `priority` column (urgent/work_in/routine) that does not match the reason-based triage_tier.
- **Reconciliation**: waitlist slot_status requires joining waitlist patients to future appointments, not just looking at requested_date.
- **Keyword boundaries**: 'Annual check' is standard, 'Annual wellness exam' is routine, 'Chronic kidney disease monitoring' is standard, and 'Ear infection re-check' is urgent. Partial or case-sensitive matching fails.
- **Cross-collection aggregation**: the final summary spans appointments, waitlist, and ops_reports.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Waitlist priority vs triage divergence: id 2 (priority 'urgent', reason 'Anal gland expression' -> standard), id 6 (priority 'routine', reason 'Ear infection re-check' -> urgent).
- Slot_status hazards: waitlist id 3 (patient 11) has future appointment id 546 (2026-09-30, scheduled); waitlist id 4 (patient 15) has future appointment id 69 (2026-09-30, confirmed). For episode 2026-09-30 both are booked.
- Stale future-dated appointments before ep: id 74 (scheduled, 2026-09-27, Ear infection re-check) and id 60 (scheduled, 2026-09-27, Chronic kidney disease monitoring).
- Keyword boundary: id 545 (scheduled, 2026-09-30, 'Annual check') is standard, not routine.
- Status decoy: id 48 (checked_in, 2026-09-04, 'Ear infection re-check') has urgent reason but is past and not scheduled/confirmed.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
