# 069_transfer_chain_consistency — REDTEAM notes

## Mission
Transfer records must form a consistent chain with patient locations. For every 'completed' transfer, the patient's CURRENT location must equal the transfer's to_location_id — unless a LATER transfer (by requested_at) also completed for the same patient, in which case only the latest completed transfer must match. Find violations and fix the TRANSFER rows only: set status 'superseded' for completed transfers that a later completed transfer replaces, and add chain_fixed='<batch_code>' to any transfer whose status you change. Never edit patients here.

## Why this is hard / unique
Temporal chain reasoning (latest-wins) with fix-the-log-not-the-patient inversion; requires modeling the chain, not pattern-matching one row.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
