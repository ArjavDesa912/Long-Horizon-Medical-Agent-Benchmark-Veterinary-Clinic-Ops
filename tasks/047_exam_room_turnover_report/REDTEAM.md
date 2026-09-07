# 047_exam_room_turnover_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Build an exam-room turnover report. For each (location_id, room) pair with appointments in the trailing 30 days or next 14 days, compute completed_last_30, booked_next_14, turnover_score, distinct patients/providers, and a primary provider with numeric tie-break. Produce a summary row with total, busiest pair, all pairs, and average turnover.

## Why this is hard / unique
- **Cross-location room identity**: room names ('Exam 1/2/3') repeat across all three locations; the report key must be (location_id, room), not room alone.
- **Half-open date windows and status filters**: the past bucket is `completed` in [ep-30, ep); the future bucket is `scheduled`/`confirmed` in [ep, ep+14). `no_show`, `checked_in`, and stale past `scheduled` rows must not leak between buckets.
- **Multi-hop metrics**: distinct patients, distinct providers, primary provider, and summary averages all require joins/aggregation across the appointment window.
- **Dual-path verification**: every number is computed both by raw-row Python and by SQL GROUP BY and must agree.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Room name collision: rows id 4 (Exam 1, location 1, checked_in), id 5 (Exam 1, location 2, checked_in), id 6 (Exam 1, location 3, checked_in) all share room 'Exam 1'.
- Trailing-30 status decoys: id 4 (checked_in, 2026-09-04, Exam 1, loc 1) and id 99 (no_show, 2026-09-03, Exam 3, loc 3) fall inside [2026-08-31, 2026-09-30) but must not count as completed.
- Stale past scheduled: id 74 (scheduled, 2026-09-27, Ear infection re-check, Exam 3, loc 2) and id 60 (scheduled, 2026-09-27, Chronic kidney disease monitoring, Exam 1, loc 3) are before episode 2026-09-30 and not in the future bucket.
- Episode-date boundary: id 545 (scheduled, 2026-09-30, Annual check, Exam 1, loc 1) is in the future bucket [ep, ep+14), not the past bucket.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
