# 084_imaging_metadata_gap_fill — REDTEAM notes

## Mission
Every files row's path must follow the convention '<patient_id>/<date-or-doctype>/<filename>' and patient_id must match the patient_id field. Find rows where path does not START WITH '<patient_id>/' and repair the path minimally: prepend '<patient_id>/' to the existing path. Add field path_fixed='<batch_code>' to repaired rows. Compliant rows stay byte-identical.

## Why this is hard / unique
Minimal-diff path repair (prepend, not rebuild); agents regenerate whole paths and lose the date/doctype segment.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
