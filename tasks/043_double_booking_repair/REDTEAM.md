# 043_double_booking_repair — REDTEAM notes (Phase 4 PENDING)

## Mission
Repair future double-booked appointments. For each future scheduled/confirmed appointment in a conflict group (same date/location/room/start_time), keep the earliest created row and shift the others by 30-minute increments until a free slot is found before 17:00; if no slot, set status to 'needs_reschedule'. Tag every moved or needs-reschedule row with the batch code, log an audit row, and write a summary `ops_reports` row.

## Why this is hard / unique
- Deterministic cascade algorithm with a hard 17:00 stop and a terminal 'needs_reschedule' state.
- Future-date filter excludes many plausible-looking conflict groups in the past.
- Must preserve inverted start/end times (e.g., 12:30-12:00) by adding 30 minutes to both.
- The winner of a group is determined by `created_at` then `id`, not by `id` alone.
- Dual-path verification of the summary counts (Python re-simulation and SQL).

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Past conflict groups such as 2026-09-16 ids 226/118, 2026-09-11 ids 256/61 must not be repaired.
- Only 'scheduled'/'confirmed' rows are candidates; completed/no_show/checked_in are ignored even if they share a key.
- The 2026-10-04 16:00 Exam 3 group (ids 38, 128, 200) is the canonical cascade: 38 keeps, 128 shifts to 16:30, 200 becomes 'needs_reschedule' because 17:00 is past the hard stop.
- The 2026-09-30 09:00 Exam 1 pair (ids 469, 545): 469 has earlier created_at and keeps; 545 shifts to 09:30.
- Appointments with end_time before start_time (e.g., id 313 12:30-12:00) must shift to 13:00-12:30, not be swapped.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
