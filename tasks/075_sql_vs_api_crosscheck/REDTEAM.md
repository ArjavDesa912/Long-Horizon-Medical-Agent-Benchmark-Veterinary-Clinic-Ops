# 075_sql_vs_api_crosscheck — REDTEAM notes (Phase 4 PENDING)

## Mission
Run a full-database row-count parity audit between the paginated REST API (`GET /v1/query/{collection}`) and the service-admin SQL endpoint (`POST /v1/sql/query`) for all 24 seeded business collections. Write per-collection `sql_crosscheck` rows and one `sql_crosscheck_summary` row keyed by the episode `batch_code`.

## Why this is hard / unique
- **Whole-database scope**, not a single table: the agent must enumerate collections, know the prefix difference between REST slugs and SQL table names, and paginate large collections.
- **Dual-path derivation**: every count is computed independently via REST and SQL and must agree before the agent's written value is accepted.
- **Runtime-table red herring**: `/v1/tables` returns `ops_meta` and, after first write, `ops_reports`. Those must be excluded or the report row count and totals are wrong.
- **Idempotent overwrite**: the agent must delete prior crosscheck rows for this batch before writing, otherwise a re-run would duplicate.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. `ops_meta` and `ops_reports` are not in the host-side seed snapshot, which contains exactly 24 collections. Including them would produce >24 report rows.
2. SQL table names are the full `veterinary_clinic_system_*` names (e.g., `veterinary_clinic_system_appointments`), while REST collection sligs are the short names; the snapshot's collection keys confirm the full names.
3. Small collections are confirmable: `audit_log` (4 rows), `controlled_substance_log` (12 rows), `reminder_queue` (4 rows) in the snapshot. Inferring counts from a single page or metadata would misreport these.
4. Large-collection parity is confirmable: `appointments` 548, `vaccinations` 600, `patients` 300, `owners` 220, `billing_invoices` 260 per the snapshot; any hardcoded count will fail unless it is freshly derived.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
