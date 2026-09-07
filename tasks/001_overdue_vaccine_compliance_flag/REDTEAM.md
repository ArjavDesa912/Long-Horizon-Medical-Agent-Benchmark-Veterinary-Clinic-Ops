# 001_overdue_vaccine_compliance_flag — REDTEAM notes (Phase 4 PENDING)

## Mission
Upgrade the v1 "set compliance_flag on all vaccinations" task to a hardmode v2 daily vaccination compliance snapshot. The agent must classify all 600 vaccination rows by a per-episode business-date window, cross-check the reminder_queue for stale queued `vaccination_due` rows without modifying them, and push an `ops_reports` summary with counts, compliance percentage, and species/location breakdowns. The entire flow is idempotent and all aggregates are verified via dual raw-row and SQL paths.

## Why this is hard / unique
- Implicit rule for `compliance_flag` derived from the live `episode_date` and a 7-day due_soon window (no counts or row IDs in the instruction).
- Multi-hop joins required for `breakdown_by_species` and `breakdown_by_location` (vaccination → patient → species/location).
- Reconciliation without mutation: the agent must read `reminder_queue`, distinguish decoy `kind` values, and count stale rows but leave them untouched.
- Dual-path verification for every aggregate number (Python filter vs SQL GROUP BY/COUNT) and strict canary checks on all collections outside the blast radius.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Decoy reminder_queue rows**: the seed snapshot contains exactly 4 `reminder_queue` rows: 2 `vaccination_due`/`queued` (patient 2 due 2026-08-14 and patient 5 due 2026-09-10), 1 `invoice_overdue`/`sent`, and 1 `boarding_checkin`/`queued`. The non-vaccination kinds and the still-valid vax rows must survive untouched.
- **Date-boundary precision**: at the default episode date 2026-09-30 the live seed contains 122 overdue and 16 due_soon vaccinations, and 20 due dates fall in the jitter band [2026-09-27, 2026-10-07]. The episode date jitters ±3 days in `env.py`, so an off-by-one boundary or a hardcoded date will produce plausible-but-wrong counts.
- **Multi-hop join and collision hazards**: 300 patients map to 5 species (canine 153, feline 90, avian 21, exotic 20, equine 16) and 3 locations. The 50-name pet-name pool means names can repeat; correct breakdowns require joining through `patient_id` and `location_id`, not pet names.
- **Idempotency on re-run**: all 600 vaccinations carry `compliance_flag` and the `ops_reports` row for the batch already exists after the first run. A second run must overwrite the same report and produce identical state.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
