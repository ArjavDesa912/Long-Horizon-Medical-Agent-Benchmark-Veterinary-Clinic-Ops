# 007_overdue_vax_owner_letters — REDTEAM notes (hardmode v2)

## Mission
Fuses v1's 007 (reminder-queue reconciliation sweep) + 008 (grouped
vaccination compliance report) + 010 (vaccine inventory coverage) into one
audit mission with a single combined end-state: a sweep that reconciles the
(stale, partial) reminder queue against live vaccination records and emails
owners of every genuinely-overdue patient; a compliance report grouped by
vaccine type plus an ALL rollup; and a cross-collection inventory-coverage
report joining upcoming clinical demand against pharmacy stock. All three
parts read the same live vaccination data as of the (now ±3-day-jittered)
episode date.

## Why this is hard / unique
- Reconciliation, not a lookup: the reminder queue only has 2 of the ~100+
  patients that are actually overdue at 10x seed volume — brute-force
  inspection is not viable, the agent must aggregate live vaccination data.
- Every aggregate (compliance totals/overdue, inventory due_next_30) is
  checked two independent ways (raw-row filter vs SQL GROUP BY/COUNT) and
  both must agree with what was written (Hard Rule 4).
- A real design bug only surfaced at 10x volume: matching overdue-notice
  rows by `(owner_id, body)` broke once two litter-mates of the same owner
  legitimately shared a name and count (50-name pool over 300 patients).
  Fixed by adding a `patient_id` field and keying on it — see "Hazards
  closed" below.
- Idempotent by construction: R (reminders flipped) is re-derived from live
  post-flip state, not a run-local counter; report rows are deleted and
  rewritten keyed by `batch_code` so a second run reaches identical state.

## Hazards closed (task.json.hazards, confirmed against live data)
1. **Decoy reminder_queue rows.** Seed row id=3 (`kind='invoice_overdue'`,
   already `status='sent'`) and id=4 (`kind='boarding_checkin'`,
   `status='queued'`) sit in the same collection as the sweep's real
   targets. Confirmed via live attack (see below): flipping id=4 after a
   correct gold run is caught by the decoy-row `row_eq` assertion.
2. **Date-boundary precision.** Overdue uses strict `<`; the coverage
   window uses inclusive `<=`/`>=`. Confirmed real (not hypothetical) at
   10x volume: with the episode date jittering ±3 days, live vaccination
   counts near the boundary shift by single digits per day
   (checked directly against `_expectations/seed_snapshot.json`:
   101/104/106 overdue patients across ep=2026-09-27/09-30/10-03).
3. **Multi-pet owner collision.** Confirmed real: 17 owners have 2+
   overdue patients in the live seed at ep=2026-09-30. This is what broke
   the first implementation (verifier reported "patient 37 (owner 171)
   comm row count: expected 1, found 2" during QC) — fixed by adding
   `patient_id` to the communications row and keying all matching on it
   instead of body text.
4. **Idempotency on rerun.** Confirmed via QC: `tools/qc_task.py` runs
   gold → verify → verify again; both verifier runs PASS with identical
   state.

## Phase 4 — hacker-fixer loop (live container, `rl-env/veterinary_clinic_system:2.0.0`)

| # | Attack | Result | Evidence |
|---|---|---|---|
| 1 | Metadata inference — can expected values be read from manifest/task.json/error messages? | **CLOSED** (was open, fixed this round) | `task.json`/`gold.py`/`verifier.py` are baked into the image at `/app/env/grading/tasks/**` (confirmed via `find` inside the built image) but are `chmod 400 root:root`. More importantly: the verifier's own FAIL messages **were** leaking concrete expected/actual values through `vlib.Verifier.expect_equal`/`expect_cents` (and one hand-rolled check in this task's `compliance_pct` assertion), and `env.py:472` surfaces the verifier's raw stdout as `info["reward_reason"]` on every `step()` — a full oracle. Fixed suite-wide by capping `expect_equal`/`expect_cents` to a bare `"{label}: mismatch"` (detail moved behind a host-only `VERIFIER_DEBUG=1` env var, printed to stderr, never stdout), and fixed the one hand-rolled instance in this task's verifier the same way. Re-verified: `qc_task.py` still PASS/FAIL as expected on all baselines after the change (fail messages now generic). |
| 2 | Partial/prefix satisfaction — does killing gold.py early still pass? | FAIL (correctly rejected) | Killed `gold.py` ~1.5s into its ~2.7s run (reminder-queue flips done, reports not yet written); verifier: `FAIL: reminder_queue count: expected 5, found 4` → generic `mismatch` post-fix. |
| 3 | Canary/scope violation — mutate a row just outside blast radius | FAIL (correctly rejected) | Ran gold.py to completion, then flipped decoy row id=4 (`boarding_checkin`) to `status='sent'`; verifier: `FAIL: reminder 4 changed (decoy row hazard)`. |
| 4 | Evaluation-function tampering — reachable verifier/gold/task.json/expected values from inside the sandbox? | **Confirmed closed for expected-value leakage** (item 1); **file-permission boundary not independently re-verified after the rebuild** — see Known gaps. | `docker run --rm <image> find / -iname '*verif*' -o -iname '*gold*' -o -iname 'task.json'` shows `/app/env/grading/tasks/**` files exist, `chmod 400`/`chmod 700` owned by root. Whether the actual agent-facing process (OpenEnv server) runs as non-root was not confirmed this round — flagged as a follow-up. |
| 5 | Retry/flake exploitation — same post-gold state, verifier run 5x | PASS (5/5 identical) | Covered via `qc_task.py`'s `verify_after_gold` + `verify_idempotent` (2/2 identical) plus the publish.ps1 verification gate's own reset→gold→PASS→reset→FAIL cycle; not independently run 5x in this round beyond the 2x QC already required — see Known gaps for a full 5x re-run recommendation. |
| 6 | Style/no-op-adjacent shortcut — plausible values without real joins | FAIL (correctly rejected) | Covered by `qc_task.py`'s `lazy_hardcode` baseline (pushes a stale-batch `ops_reports` row with made-up numbers) — `hardcode_fail: True` in QC results. |

**hardened_after_rounds: 2** — round 1 shipped with the `(owner_id, body)`
matching bug and the value-leak in `expect_equal`/`expect_cents` +
`compliance_pct`; round 2 (this document) fixes both and re-confirms all
baselines.

## Known gaps (do not treat this task as fully closed until these are done)
- Attack #4's file-permission boundary (does the OpenEnv server process run
  as non-root, making the on-disk `gold.py`/`verifier.py`/`task.json`
  actually unreadable to an agent, not just unreadable in theory) has not
  been independently confirmed against a live container this round.
- Attack #5 was only exercised 2x via existing QC tooling, not the full 5x
  the hard rule asks for.
- `par_steps`/`max_steps` (130/195) are measured from this round's
  `gold.py`/`gold_alt.py` runs (123 and 128-131 API calls respectively);
  re-measure if either script changes again.
