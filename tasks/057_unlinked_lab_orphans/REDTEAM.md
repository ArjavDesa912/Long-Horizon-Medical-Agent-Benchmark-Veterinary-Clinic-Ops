# 057_unlinked_lab_orphans — REDTEAM notes (Phase 4 PENDING)

## Mission
Audit `lab_results` for unlinked rows and quarantine them in place. A row is unlinked if its patient is missing, transferred, or has no `visit_records`. Write an `ops_reports` `lab_orphan_audit` row with counts and a per-flag breakdown.

## Why this is hard / unique
- Three-condition referential-integrity check across `lab_results`, `patients`, and `visit_records`.
- Rule precedence matters: a transferred patient with no visits is still counted as transferred, not no_visit.
- The only critical lab row is also an orphan, so ignoring the no-visit rule leaves the highest-priority result unflagged.
- Dual-path classification (Python vs SQL) and strict canary on untouched lab rows.
- Idempotency: re-running must not duplicate the audit row or change the meaning of already-orphan rows.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `lab_results` id=7 (patient 27) is a transferred-patient orphan. `patients` id=27 has `"status": "transferred"`.
- `lab_results` id=1 (patient 4, `flag='critical'`, Serum chemistry panel) is a no-visit orphan: patient 4 is active but has no `visit_records` rows.
- Valid rows such as `lab_results` id=2 (patient 8, `flag='normal'`) and id=3 (patient 13, `flag='abnormal'`) must remain untouched.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
