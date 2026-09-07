# 053_problem_list_rollup — REDTEAM notes (Phase 4 PENDING)

## Mission
Build the active-problem census under the episode batch code. Only problems-array
entries with status='active' count. Write two ops_reports sets for this batch
(delete-then-rewrite keyed on batch_code): (1) 'problem_census' — one row per
active problem name with active_cases, distinct_patients, distinct_locations, and
distinct_species (the last needs the patients join); (2)
'problem_census_by_location' — one row per (problem, location_id) cell with
active_cases and distinct_patients. Nothing else changes.

## Why this is hard / unique
- Nested JSON-array aggregation with a strict status filter across 371 visit
  rows, 208 of which carry empty problems arrays.
- Rows-vs-distinct-patients asymmetry is real in the seed (patient 59 has the
  same active problem on two visit rows).
- Three distinct-count dimensions at the top level, one requiring a cross-
  collection join to patients.species.
- Full dual-path verification: every number is computed via a raw-row Python
  pass AND an independent SQL json_array_elements + GROUP BY; three-way
  agreement required.
- Idempotent rewrite per batch_code.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Patient 59 has 'atopic dermatitis' status='active' on visit ids 118 AND 331 —
  that name must report active_cases=15, distinct_patients=14.
- Resolved-status decoys exist under the same names: visit id=1 'chronic kidney
  disease' (resolved), id=19 'obesity' (resolved), id=20 'atopic dermatitis'
  (resolved) — name-only filtering inflates counts.
- 208 of 371 visit rows have problems=[] — must be skipped without error.
- Species mixes differ per problem (chronic kidney disease spans 5 species,
  hypothyroidism 3, obesity 4) — distinct_species cannot be guessed from
  distinct_patients.
- All 7 names appear at all 3 locations (21 cells) but with different counts,
  e.g., atopic dermatitis 7/6 at loc 1 vs 1/1 at loc 3 — fabricated uniform
  cells fail.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.

### Live-QC assumptions to verify
- The SQL path uses `json_array_elements(v.problems::json)` — the `::json` cast
  makes it work whether `problems` is stored as json, jsonb, or JSON text —
  plus `pt.id::text = v.patient_id::text` for the patients join. If the
  Stackhouse SQL endpoint rejects lateral function joins or casts, the QC
  session must swap in an equivalent independent SQL formulation.
- Real gold step counts still need measuring; par_steps/max_steps are null in
  task.json by design.
