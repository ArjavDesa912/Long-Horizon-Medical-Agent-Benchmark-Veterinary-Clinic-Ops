# 083_file_storage_audit — REDTEAM notes

## Mission
Storage audit for the practice's file metadata. One ops_reports row per bucket present in the files collection: {report: 'storage_audit', batch_code, bucket, file_count, total_bytes: <sum size_bytes>, total_mb: <round(total_bytes /1048576, 2)>, doc_types: <comma-joined sorted distinct doc_type values>}.

## Why this is hard / unique
Byte-to-MB unit conversion (1048576, not 1000000) and sorted distinct lists.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
