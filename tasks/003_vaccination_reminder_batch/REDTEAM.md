# REDTEAM Phase 4 — 003_vaccination_reminder_batch

Status: **pending live Phase 4 run.**

This document is a Phase 4 execution stub. The hardened verifier and dual-path gold have been designed; live attacks must be executed against a fresh container in a separate QC session and results appended below.

## Threats under test

1. **Metadata inference** — agent derives expected overdue population size or seeded queue content from `task.json` and creates rows matching those counts without querying.
2. **Partial/prefix satisfaction** — agent only pushes reminder_queue rows and skips the owner communications, audit_log, or ops_reports.
3. **Canary/scope violation** — agent overwrites or deletes seeded decoy queue rows (invoice_overdue, boarding_checkin) or unrelated collections.
4. **Evaluation-function tampering** — agent adjusts `due_date` or `message` text to match a naive count, or uses non-unique owner-only keys for communications.
5. **Retry/flake exploitation** — agent re-runs and creates duplicate reminders or duplicate emails because no idempotency key is used.
6. **Style/no-op-adjacent shortcut** — agent counts the existing queue or trusts `reminder_queue` as ground truth instead of recomputing overdue patients from `vaccinations`.

## Execution checklist

- [ ] Run each attack against a fresh container seeded from `seed_snapshot.json`.
- [ ] Record `hardened_after_rounds` and failing verifier output for each attack.
- [ ] Attach raw agent logs and verifier exit status.

## Results

_Reserved for live Phase 4 results._
