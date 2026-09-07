# 076_weekly_schedule_load_balance — REDTEAM notes (Phase 4 PENDING)

## Mission
For the 7-day inclusive window starting on the episode date, produce a load-balance report for the practice: one row per veterinarian (appointment count, scheduled hours, unique patients, busiest day, home location), one row per clinic location (total appointments, hours, unique vets and patients, busiest day), and one summary row with the most/least loaded veterinarians and the load-balance ratio.

## Why this is hard / unique
- **Multi-collection join**: appointments must be joined to providers (role + name + home location), patients (for unique counts), and locations (for location names and per-location aggregation).
- **Provider vs appointment location mismatch**: a veterinarian's home `location_id` is not necessarily the `location_id` of their appointments, so the per-provider and per-location rows must be built from different keys.
- **Dual-path verification**: every per-vet and per-location aggregate is derived independently via raw-row Python and SQL GROUP BY, and the two paths must agree.
- **Tiebreak rules**: busiest_day and most/least loaded provider use explicit tiebreaks, not arbitrary picks.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Non-veterinarian providers**: provider rows 5-9 are `vet_tech`, `kennel_attendant`, or `groomer`; only ids 1-4 are `veterinarian` in the snapshot.
2. **Provider location vs appointment location**: provider id=1 has `location_id=1` in the providers table, but in the 2026-09-30 window it has appointments at location_id=2 (ids 128, 149, 200, 212) and location_id=3 (id 120). Using the appointment's location for the per-provider row is wrong.
3. **Duplicate patients per vet in the same week**: patient 212 has two appointments with provider 3 in the 2026-09-30 window; patient 204 has two appointments with provider 4. Counting appointments instead of distinct `patient_id` overstates `unique_patient_count`.
4. **Status/date filtering**: the seed contains 176 `completed` and 66 `no_show` appointments on past dates; the actual episode windows only contain `scheduled`/`confirmed` future appointments, but the rule must still be applied.
5. **All three locations must appear**: even a location with zero window appointments must get a `weekly_load_location` row, otherwise the report is incomplete.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
