# 054_weight_trend_alert — REDTEAM notes (Phase 4 PENDING)

## Mission
Screen all patients for significant weight drift under the episode batch code:
per patient, order visits by (visit_date, created_at, id) and compare earliest vs
latest weight_kg; a strictly >10% relative change flags the patient. Each flagged
patient gets (a) the exact alert 'Weight change >10% — review diet plan' appended
to its alerts array (preserve existing, no dupes), (b) a waitlist row
{reason:'Weight recheck — flagged trend', priority:'work_in', status:'waiting',
requested_date = episode date + 14 days, patient's location} created only if that
patient has no matching waiting row, and (c) one 'weight_alert' ops_reports row
for the batch with first/latest/change_pct/direction. Everything else unchanged.

## Why this is hard / unique
- Strict >10% threshold with real near-boundary decoys in the seed (-8.11% and
  +9.38% patients must NOT flag).
- Three write surfaces: append-only patient alerts, dedup-guarded waitlist rows,
  and a delete-then-rewrite report set — all must stay consistent with one
  flagged set.
- Dual-path flagged-set derivation: raw-row Python sort AND SQL DISTINCT ON
  first/last weights must agree three-way with the written rows.
- Name collisions at 10x patient volume make patient_id the only safe join key.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Near-threshold non-flags: patient 25 'Sage' 37→34 kg (-8.11%), patient 189
  'Buddy' 32→35 kg (+9.38%).
- Alerts-preservation: patient 13 'Hazel' is flagged (-50.0%) and already carries
  alerts=['Allergic to penicillins'] — overwrite destroys it.
- Name collisions among flagged patients: 'Rex' (108, 267), 'Loki' (96, 185),
  'Winston' (38, 64), 'Toby' (205, 289).
- 91 patients have exactly 1 visit and 98 have zero — single weights are not a
  trend.
- Seeded waitlist ids 1-6 (unrelated reasons) must stay byte-identical and do
  NOT satisfy the dedup check (dedup keys on exact reason + status='waiting').
- 97 flagged patients in the current seed — a large, idempotent write set.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.

### Live-QC assumptions to verify
- The SQL path relies on Postgres DISTINCT ON subqueries through
  /v1/sql/query — consistent with the reference task's verified SQL usage; if
  the endpoint rejects subselects/ORDER BY inside DISTINCT ON, the QC session
  must swap in an equivalent independent formulation.
- All weight values are numeric in the seed; `weight_kg` SQL ordering uses the
  column directly.
- Real gold step counts still need measuring; par_steps/max_steps are null in
  task.json by design.
