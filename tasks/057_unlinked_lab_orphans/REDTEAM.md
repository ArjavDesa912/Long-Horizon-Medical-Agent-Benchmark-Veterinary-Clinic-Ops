# 057_unlinked_lab_orphans — REDTEAM notes

## Mission
Data hygiene: every lab_results row must reference a patient that exists AND is not status 'transferred' (transferred patients' results belong to the receiving clinic). Find orphan rows (patient_id missing from patients, or pointing at a transferred patient) and mark them orphan=true with orphan_note='<batch_code>'. Do not delete anything; do not modify valid rows.

## Why this is hard / unique
Referential-integrity audit across collections with a non-obvious second condition (transferred status).

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
