# 031_cs_administer_witnessed_entry — REDTEAM notes

## Mission
Log a controlled-substance administration per DEA recordkeeping practice (every administration recorded with a witness — look up the convention if unsure): 0.2 units of Buprenorphine were administered to patient 4 (Noodle) for post-dental pain. Append one row to controlled_substance_log: item_name 'Buprenorphine', location_id '1', action 'administer', quantity 0.2, witnessed_by 'Rosa Delgado', performed_by 'Dr. Alvarez', occurred_at on the episode date, patient_id '4', notes 'Post-dental analgesia <batch_code>' (batch code from ops_meta). Append only — never edit existing log rows.

## Why this is hard / unique
Append-only DEA log discipline; the seeded row shape must be matched exactly while embedding the live nonce.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
