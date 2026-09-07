# 042_waitlist_promotion — REDTEAM notes (Phase 4 PENDING)

## Mission
Promote the single highest-priority waiting waitlist entry at location 1 into the earliest free 30-minute slot at location 1 on the episode date (09:00 or later; rooms Exam 1, then Exam 2, then Exam 3). Create one appointment, mark the winner 'booked', leave all other entries 'waiting', and write one audit_log and one ops_reports row for this batch.

## Why this is hard / unique
- Schedule-aware: the agent must search for the first free slot at a specific location on a specific date, not use a hardcoded room/time.
- Priority ordering with tiebreakers; `requested_date` is a decoy field and must not determine the winner.
- Single-winner idempotency: a rerun must not promote the second loc1 entry or duplicate the appointment/audit.
- Multiple collections updated in a coordinated workflow.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Waitlist id 1 (location 1, urgent, created_at 2026-09-04T21:08:40.020847+00:00) wins over id 4 (location 1, work_in, created_at 2026-09-04T21:08:40.030219+00:00). Priority, not requested_date, must order them.
- Waitlist ids 2, 3, 5, 6 are at locations 2/3 and must remain 'waiting'.
- On 2026-09-30 the 09:00 Exam 1 slot at loc1 is occupied by appointment ids 469 and 545, so the first free slot is Exam 2 at 09:00; an agent that hardcodes Exam 1/09:00 creates a double-booking.
- Appointments with status completed/no_show are not blockers; only scheduled/confirmed/checked_in appointments block.
- Provider must be id 1.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
