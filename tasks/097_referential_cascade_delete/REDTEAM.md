# 097_referential_cascade_delete — REDTEAM notes

## Mission
Privacy erasure request (GDPR-style right to erasure, vet-clinic analogue): owner id 22 (Faye Lovelace) requests full deletion. Delete: the owner row; all patients of that owner; and every appointments, visit_records, vaccinations, medications, lab_results, billing_invoices, communications, waitlist, boarding_reservations, and files row that references the owner or any of the owner's patients. Then push one ops_reports row {report: 'erasure', batch_code, owner_id: '22', patients_removed: <count>, rows_removed_total: <count including the owner row>}. Every row not related to owner 22 must remain byte-identical.

## Why this is hard / unique
Transitive cascade delete across 11 collections with an exact preservation guarantee; partial cascades (forgetting files or waitlist) are the expected failure.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
