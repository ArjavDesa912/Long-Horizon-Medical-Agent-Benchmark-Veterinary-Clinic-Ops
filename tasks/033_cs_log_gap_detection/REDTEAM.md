# 033_cs_log_gap_detection — REDTEAM notes

## Mission
Audit the controlled-substance log for DEA witness-compliance gaps: every row with action 'administer' or 'waste' must have a real witnessed_by value (not null, not '', not '—'), because administration and waste require a witness while receive and dispense do not (verify the convention if needed). Fix violations minimally: set witnessed_by to 'Dr. Alvarez' and add field witness_corrected='<batch_code>'. Rows already compliant and all receive/dispense rows must remain byte-identical to seed.

## Why this is hard / unique
Rule-conditioned repair where the compliant set is defined by domain knowledge (receive/dispense exempt); over-fixing compliant rows fails byte-identity.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
