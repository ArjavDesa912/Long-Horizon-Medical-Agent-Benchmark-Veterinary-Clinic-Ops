# 050_schedule_density_rebalance — REDTEAM notes (Phase 4 PENDING)

## Mission
Practice-wide schedule density rebalance under the episode batch code. Per location
(1, 2, 3), independently and from a single pre-move snapshot: bucket future
(appointment_date >= episode_date) rows with status 'scheduled'/'confirmed' by day;
if the busiest day holds strictly more than 4, move that day's latest-starting
'scheduled' row (start_time tie -> lowest id) to the sparsest bucketed day
(day tie -> earliest) and stamp rebalanced=<batch_code>; otherwise write one
ops_reports row {report:'rebalance', batch_code, location_id, moved:0}. No other
changes anywhere.

## Why this is hard / unique
- The trigger branch varies per location AND per episode: the episode_date nonce
  jitters +/-3 days around 2026-09-30, so location 1 and location 3 flip between
  "move" and "write the no-op report" across episodes while location 2 always
  moves — a memorized action set is wrong, not just stale.
- Dual-path density verification: post-move per-day counts are checked against a
  seed simulation, a REST-aggregated live count, and a SQL GROUP BY — all three
  must agree.
- Row-identity enforcement: exactly one appointment may differ per triggered
  location, and only in appointment_date + rebalanced; every other row is
  byte-identical, so moving the wrong row (or an extra one) fails even when the
  aggregate density happens to match.
- Idempotent re-run: the rebalanced=<batch_code> stamp is the only safe marker;
  a second run must not move the next-latest candidate.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- 2026-10-04 at location 2: ids 38 and 200 are 'scheduled' at 16:00 while id=128
  is 'confirmed' at the same 16:00 — confirmed counts toward density but is never
  the moved row, and the id-tiebreak picks 38.
- 2026-09-30 at location 1: 11 qualifying rows; the moved row must be id=295
  (scheduled, 15:30) — id=352 (scheduled, 15:00) and confirmed id=112 (14:30) are
  wrong-row decoys on the same day.
- id=23 (location 2, 2026-08-25, 'no_show') is past-dated AND wrong status —
  a double decoy.
- At ep=2026-10-01..10-03, location 1's busiest bucket is exactly 4 (2026-10-01:
  ids 436, 442, 472, 544) — 'strictly more than 4' means the no-op branch fires;
  a '>=' boundary errors here.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.

### Live-QC assumptions to verify
- `location_id`, `status`, `start_time`, `appointment_date` are queryable SQL
  columns (consistent with the live-verified reference task's SQL usage).
- `rebalanced` and `ops_reports` fields are checked via REST document reads only
  (they are episode-written fields; not assumed to be SQL columns).
- Real gold step counts still need measuring; par_steps/max_steps are null in
  task.json by design.
