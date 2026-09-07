# 077_data_freshness_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Produce a full freshness ranking of all 24 seeded business collections. For each collection, report the newest `updated_at` timestamp and a `freshness_rank` from 1 (oldest) to 24 (newest), plus a summary row identifying the oldest and newest collections.

## Why this is hard / unique
- **Sub-second timestamp ordering**: all collections were last updated on the same calendar day within seconds of each other, so the agent must use the full `updated_at` string to determine the rank.
- **Dual-path derivation**: the verifier computes `MAX(updated_at)` both by iterating the full fetched rows and by SQL, requiring the two to agree.
- **Scope discipline**: the runtime `ops_meta` table and the report table `ops_reports` must be excluded, even though they may appear in `/v1/tables`.
- **Rank consistency**: the agent cannot stop at identifying the single oldest and newest collection; it must assign a correct rank to every collection.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Date-prefix trap**: the snapshot `updated_at` values are all `2026-09-04T21:08:xx.xxxxxx+00:00`; the oldest is `locations` (21:08:33.368278) and the newest is `audit_log` (21:08:41.394800). Comparing only the first 10 characters makes every collection equal and the rank undefined.
2. **Runtime tables**: `ops_meta` and `ops_reports` are not in the snapshot (the snapshot has exactly 24 business collections) but appear live in `/v1/tables` after reset/writes. Including them produces the wrong row count and wrong oldest/newest names.
3. **created_at vs updated_at**: every row carries both `created_at` and `updated_at`; the task requires `updated_at` specifically.
4. **SQL table names**: the SQL endpoint requires the full `veterinary_clinic_system_*` name, not the short REST slug.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
