# 089_document_expiry_tracker — REDTEAM notes

## Mission
Rabies certificates expire with the vaccination they certify. For every files row with doc_type 'rabies-certificate', find the patient's LATEST rabies vaccination due_date — the certificate's effective expiry (certificates follow the vaccine's validity, standard practice — verify if unsure). Create one ops_reports row {report: 'doc_expiry', batch_code, certificates: <count of rabies-certificate files>, expired: <how many have latest rabies due_date strictly before the episode date OR the patient has no rabies vaccination>, expiring_within_30d: <due_date in [episode date, episode date+30]>, patient_ids_expired: <comma-joined ascending patient ids of the expired set, or ''>}.

## Why this is hard / unique
Certificate-validity-follows-vaccine domain rule + three-way bucketing with an id listing.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
