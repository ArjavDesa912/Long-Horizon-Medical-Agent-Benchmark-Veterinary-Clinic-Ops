# 040_controlled_refill_freeze — REDTEAM notes

## Mission
Policy freeze: no controlled-substance prescription may carry refills once it has been active over 90 days (consistent with DEA caution around schedule III–V refills — verify if unsure). For every medication row with is_controlled_substance true, active true, and prescribed_at more than 90 days before the episode date: set refills_remaining to 0 and add field refill_frozen='<batch_code>'. Log one audit_log row per affected prescription: {actor: 'system', actor_role: 'system', action: 'REFILL_FREEZE', target_collection: 'medications', target_id: <medication id as string>, details: 'Refills frozen for <drug_name> (<batch_code>)', occurred_at: episode timestamp}. Younger or inactive prescriptions are untouched.

## Why this is hard / unique
Age-in-days threshold on a timestamp field + paired audit entries; domain-knowledge framing with a data-derived target set.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
