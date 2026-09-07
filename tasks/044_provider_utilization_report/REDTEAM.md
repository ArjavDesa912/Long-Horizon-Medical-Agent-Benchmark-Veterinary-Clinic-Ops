# 044_provider_utilization_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Build a per-veterinarian utilization report. For every provider with role 'veterinarian', push one ops_reports row with total, completed, no_show, and upcoming counts plus completed_rate and no_show_rate percentages. Providers who are not veterinarians are decoys and must be excluded.

## Why this is hard / unique
- Only 4 of 9 providers are veterinarians; the other 5 roles are decoys.
- `upcoming` is a compound date + status filter; the episode date jitters.
- Rates are percentages rounded to one decimal and must be 0.0 when total is 0.
- Dual-path derivation (Python and SQL) on four separate aggregations.
- Read-only with respect to appointments/providers; only ops_reports is written.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Provider ids 1-4 are veterinarians with non-zero appointment counts (id 1: 101 total, 26 completed, 12 no_show; id 2: 77; id 3: 198; id 4: 172).
- Provider ids 5-9 (Rosa Delgado, Miles Turner, Josie Baker, Hank Willis, Lucy Tran) have roles vet_tech, kennel_attendant, groomer and have zero appointments.
- All appointments are assigned to veterinarian provider_ids; no non-vet provider has appointments, so including them would produce all-zero rows.
- The `upcoming` count changes with episode date (e.g., for id 1: 18 at 2026-09-27, 12 at 2026-09-30, 4 at 2026-10-03).
- Rates must be rounded to one decimal (e.g., id 1 no_show_rate at ep 2026-09-30 is round(100*12/101,1)=11.9).

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
