# 055_amendment_chain_repair — REDTEAM notes (Phase 4 PENDING)

## Mission
Repair the locked-visit-note amendment chain for this episode. Detect every locked `visit_records` row whose `updated_at` is later than its `locked_at`, leave the original untouched, append a linked amendment row in `visit_records`, and produce an `ops_reports` `amendment_chain` summary row with counts and a per-location breakdown.

## Why this is hard / unique
- Forensic rule is implicit in the timestamps, not stated as a row list.
- Originals must remain byte-identical; the correct action is append-only.
- Large blast radius (344 amendments) makes manual inspection infeasible.
- Re-run idempotency and duplicate-prevention are required.
- Dual-path (Python filter vs SQL) verification on all derived counts.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `visit_records` id=371 has `locked_at:null` and an empty `plan`; it is an incomplete note but not a tampered locked note (row-level evidence: `"locked_at": null, "plan": ""`).
- Multiple unlocked rows (e.g., id=27, 57, 86, 90, 114) have `locked_at:null` and must not receive amendments.
- `audit_log` has 4 rows (TRANSFER_COMPLETED, OWNER_MERGE, CS_LOG_APPENDED, ESTIMATE_CONVERTED) and none target `visit_records`, so an agent relying on the audit log will find nothing.
- The timestamp comparison must be string-compare of ISO 8601 `updated_at > locked_at`; in this seed all 344 locked rows are tampered, but `updated_at` is the build timestamp and `locked_at` is an earlier date.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
