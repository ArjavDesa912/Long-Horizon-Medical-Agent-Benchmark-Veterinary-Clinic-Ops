# 028_draft_invoice_purge — REDTEAM notes (Phase 4 PENDING)

## Mission
Purge every draft document from both `billing_invoices` and `billing_estimates`, push one cancellation communication per deleted document, and write a `draft_purge` ops_reports row with counts, affected owners/patients, document details, and a location breakdown.

## Why this is hard / unique
- Fuses delete, create, and aggregation into one mission across two billing ledgers.
- Byte-identical survivor checks force surgical deletes, not bulk re-inserts.
- Cancellation communications must be exact and one per document.
- The report must re-derive the purge set from the seed because the live rows are gone.
- Dual-path verification uses the seed snapshot (Python) and live SQL survivor counts.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Small target, large survivor set**: `billing_invoices` has 1 draft (INV-1003, owner 3, patient 3, location 3, total $546.00, due 2026-09-23) and 259 non-draft rows (257 paid, 2 sent). `billing_estimates` has 30 draft rows and 70 non-draft rows (40 sent, 20 accepted, 10 declined). A solution that deletes the wrong status or deletes-and-re-inserts survivors will fail the byte-identity canary.
- **Cross-ledger hazard**: The agent must purge both invoices and estimates. A v1-style solution that only purges `billing_invoices` will leave 30 draft estimates behind.
- **One communication per document**: Each of the 31 deleted documents has a distinct owner and patient in this seed, but the code must not collapse by owner or skip the estimate drafts. The verifier checks the count and each body contains the exact document number.
- **Affected lists must come from deleted documents only**: `affected_owners` should be the sorted distinct owner ids of the 31 draft documents, not all 31+ owners or all 220 owners.
- **Idempotency on re-run**: After the first run there are no draft documents left. The gold detects an existing `draft_purge` report and replays the affected_documents list instead of re-querying for live drafts, avoiding a zero-count re-run bug.
- **Location breakdown**: Uses `locations.name` (Main Street Animal Hospital, Riverside Veterinary Clinic, Cedar Park Animal Care Center) for the 31 deleted documents, not raw `location_id`.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
