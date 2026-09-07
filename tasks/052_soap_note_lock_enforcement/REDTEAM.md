# 052_soap_note_lock_enforcement — REDTEAM notes (Phase 4 PENDING)

## Mission
Clinical-record lockdown under the episode batch code: every visit_records row
more than 30 days old (strictly) with locked_at null gets locked_at=<episode
timestamp> + lock_reason='retention_policy'; each lock appends one RECORD_LOCKED
audit_log row keyed to that visit id; and ops_reports gets exactly one
'lock_audit' row for the batch with records_scanned / locked_this_run /
already_locked / unlocked_recent. All other rows and collections unchanged.

## Why this is hard / unique
- Strict '>30 days' boundary interacts with the ±3-day episode_date jitter: a
  boundary row flips in/out of the target set across episodes, so a memorized
  target list is wrong, not just stale.
- Three write surfaces with different idempotency semantics: conditional row
  updates (self-suppressing on re-run), append-only audit rows (self-suppressing
  because the target set empties), and a delete-then-rewrite summary row.
- Dual-path verification: the four summary counters are recomputed via raw-row
  Python filtering AND independent SQL COUNTs; row-level byte-identity catches
  over/under-locking even when counts happen to agree.
- 1:1 audit coverage: audit target_ids must equal the lock target set exactly —
  locking extra rows inflates both surfaces.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- visit_records id=352 (visit_date 2026-08-30, locked_at null): exactly 30 days
  old at ep=2026-09-29 (must stay unlocked, unlocked_recent=1) but lockable at
  ep>=2026-09-30 — the boundary knife-edge.
- 344 of 371 seeded visit rows are already locked (e.g., id=1, visit_date
  2026-01-05, locked_at 2026-01-06T21:08:36.204+00:00) — re-stamping or adding
  lock_reason fails byte-identity.
- Lockable rows include empty problems arrays (ids 27, 352 — problems=[]) — a
  content-driven scan misses them; the rule is visit_date + locked_at only.
- Seeded audit_log ids 1-4 (TRANSFER_COMPLETED, OWNER_MERGE, CS_LOG_APPENDED,
  ESTIMATE_CONVERTED) are byte-identical decoys beside the new RECORD_LOCKED rows.
- At ep=2026-09-30 the target set is 27 rows (ids incl. 27, 57, 86, ..., 352,
  371); the set changes under jitter (26 at ep=2026-09-29).

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.

### Live-QC assumptions to verify
- SQL used in verifier touches only seeded columns (locked_at, visit_date,
  COUNT(*)); `lock_reason` is checked via REST row reads because it is an
  episode-written field.
- `visit_date >= '<cutoff>T00:00:00.000Z'` timestamptz comparison behaves as
  expected through /v1/sql/query.
- Real gold step counts still need measuring; par_steps/max_steps are null in
  task.json by design.
