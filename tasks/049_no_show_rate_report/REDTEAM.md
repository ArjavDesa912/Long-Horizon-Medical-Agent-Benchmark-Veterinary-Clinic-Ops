# 049_no_show_rate_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Produce a provider-segmented no-show analysis. For each provider with past appointments, compute outcomes (completed/no_show/checked_in), no_shows, stale_bookings (scheduled/confirmed past slots), no_show_pct, and top_no_show_reason; then create a summary row with overall stats and the highest no-show provider.

## Why this is hard / unique
- **Status-partitioned denominator**: the no-show rate uses only resolved/attended outcomes, not all past appointments. Stale scheduled/confirmed past bookings are counted separately, forcing a reconciliation between the appointment calendar and actual outcomes.
- **Provider segmentation with tie-breaks**: top reason is alphabetical tie-break; highest provider is numeric provider_id tie-break.
- **Dual-path**: every number and top reason is computed both by raw-row Python and SQL.
- **10x appointment volume**: at 548 appointments the aggregates cannot be eyeballed; the agent must query and group.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Stale past bookings: id 74 (provider 3, scheduled, 2026-09-27, Ear infection re-check) and id 60 (provider 2, scheduled, 2026-09-27, Chronic kidney disease monitoring) are past-dated scheduled rows.
- Attended outcome decoys: id 4 (provider 1, checked_in, 2026-09-04, Chronic kidney disease monitoring) and id 5 (provider 1, checked_in, 2026-09-04, Ear infection re-check) are past checked_in rows that count as attended outcomes.
- Episode-date boundary: id 545 (provider 1, scheduled, 2026-09-30, Annual check) is on the episode date and not a past appointment.
- Provider-level distribution from the snapshot for episode 2026-09-30: provider 1 outcomes=41/no_shows=12; provider 2 outcomes=36/no_shows=11; provider 3 outcomes=96/no_shows=20; provider 4 outcomes=79/no_shows=23; stale bookings are 48, 29, 79, 77 respectively.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
