# 066_owner_contact_normalization - REDTEAM notes (Phase 4 PENDING)

## Mission
Normalize every owner contact for an SMS migration: phone to '+1' + last 10 stripped digits, email lowercased, contact_normalized tag on every row. Then run a contact-quality audit (ops_reports summary), enqueue reconciliation reminders for duplicate phones, and write an audit_log entry.

## Why this is hard / unique
- Deterministic string normalization across 220 owners, with exact punctuation stripping.
- Real collision: two owners share the same phone and must be flagged, not merged.
- Multi-collection write (owners, ops_reports, reminder_queue, audit_log) with idempotent re-run.
- Dual-path verification of the normalization and duplicate counts.

## Hazards planted (task.json.hazards) - confirmed against seed_snapshot.json
- All 220 owner phones contain punctuation; e.g. owner 1 is '(828) 555-0101', owner 100 is '(828) 555-1099'.
- Owners 1 and 22 both have phone '(828) 555-0101' -> normalized '+18285550101'.
- All 220 owners have non-empty emails, so missing_email_count = 0.

## Phase 4 - NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
