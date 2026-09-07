# 063_duplicate_owner_merge — REDTEAM notes (Phase 4 PENDING)

## Mission
Merge duplicate owner records by phone-digit and lowercased email matching, repoint all child records across patients, billing_invoices, billing_estimates, communications, and reminder_queue, conserve balances, delete duplicates, and produce OWNER_MERGE audit and owner_merge ops_report rows.

## Why this is hard / unique
- Entity resolution with normalization: phone numbers and emails must be normalized before comparison.
- Multi-collection foreign-key repointing: the merge touches five child collections.
- Balance conservation and survivor selection by `created_at` (not id) add subtle constraints.
- `ops_reports` row must accurately count the repoints, which can only be verified against the seed snapshot.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Single duplicate cluster**: owners 1 and 22 share normalized phone `8285550101` (both `(828) 555-0101`). Owner 1 is Margaret Whitfield (`margaret.whitfield@example.com`, balance 134.0, created earlier). Owner 22 is Faye Lovelace (`faye.lovelace@example.com`, balance 0.0, created later). Confirmed from `veterinary_clinic_system_owners`.
- **Child records for owner 22**: patients 26, 168, 170; billing_invoices 22 and 242; billing_estimates 19; communications 22. Confirmed by scanning `veterinary_clinic_system_patients`, `billing_invoices`, `billing_estimates`, and `communications` for `owner_id='22'`.
- **Balance-weakness note**: owner 22's balance is 0.0, so a lazy merge that does not sum balances still yields 134.0. The repoint and audit checks carry the real weight.
- **Survivor rule**: owner 1 has the earlier `created_at` timestamp (2026-09-04T21:08:33.689878+00:00 vs 2026-09-04T21:08:34.144830+00:00).

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
