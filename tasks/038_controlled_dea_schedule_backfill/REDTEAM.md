# 038_controlled_dea_schedule_backfill — REDTEAM notes (Phase 4 PENDING)

## Mission
DEA schedule backfill plus compliance sweep: find the controlled `medications`
rows missing `dea_schedule`, fill each with the modal schedule of its
`drug_name` siblings (fallback to published DEA schedule if a drug has no
scheduled siblings — never triggered in this seed), tag only the changed rows
with `schedule_fixed`, emit one `ops_reports` `dea_backfill` row per
controlled drug plus a `dea_backfill_summary` row, and append one
`DEA_SCHEDULE_BACKFILL` `audit_log` row.

## Why this is hard / unique
- The missing row is a needle in 200 medications rows (50 controlled): the
  agent must filter, not eyeball.
- The correct value is *derived from siblings* (Alprazolam: 13 x 'IV', 1
  missing → modal 'IV'), and the schedule format must be copied verbatim —
  bare Roman numerals, not '4' or 'Schedule IV'.
- Row-level precision: the 49 already-scheduled controlled rows must remain
  byte-identical and must NOT gain `schedule_fixed`.
- Dual-path verification on controlled_count and modal schedule; a post-fix
  "zero unfilled" invariant checked via both REST and SQL.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Exactly one controlled row is missing `dea_schedule`: medications id 2
  (Alprazolam, patient_id '1', is_controlled_substance true, dea_schedule
  null). Verified — the other 49 controlled rows all carry a schedule.
- Modal derivation evidence: snapshot controlled counts per drug are
  Alprazolam {IV:13, MISSING:1}, Buprenorphine {V:12}, Tramadol {IV:15},
  Ketamine {III:9} — the mode is unambiguous and must come from siblings.
- `pharmacy_inventory` ids 35-42 carry their own `dea_schedule` values (V,
  IV, III, IV) — a decoy system of record; the canary on that collection
  catches any agent that "fixes" the wrong table.
- Zero non-controlled rows carry a schedule (verified: 150 non-controlled
  rows all have dea_schedule null) — any added schedule/tag on them fails
  the byte-identical check.
- `audit_log` id 3 is `CS_LOG_APPENDED` (controlled-substance-looking) —
  decoy; it must be untouched and exactly one new audit row is allowed.
- `ops_reports` is absent from the 24-collection snapshot — created blind.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.
