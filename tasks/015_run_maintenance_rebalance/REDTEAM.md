# 015_run_maintenance_rebalance — REDTEAM notes

## Mission
The kennel needs a deep-clean rotation. At each location, take the lowest-numbered AVAILABLE kennel run (run_type 'kennel') and set its status to 'maintenance'. Additionally, at the location that currently has the MOST occupied runs, also set the highest-numbered available 'large_dog' run to 'maintenance' if one exists there. Do not touch occupied or cleaning runs, and make no other changes.

## Why this is hard / unique
Two-level conditional (per-location argmin + global argmax side rule); picking by run_number string vs numeric is the trap.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
