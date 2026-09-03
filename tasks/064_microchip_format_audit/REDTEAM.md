# 064_microchip_format_audit — REDTEAM notes

## Mission
Audit microchip registrations against ISO 11784 (15 numeric digits — verify online if unsure). For every patient whose microchip_id is missing, null, or not exactly 15 digits, set microchip_flag='non_compliant' and microchip_flagged='<batch_code>'. Compliant patients stay byte-identical; do not invent new chip numbers.

## Why this is hard / unique
Format validation from an external standard; flag-without-inventing is the discipline under test.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
