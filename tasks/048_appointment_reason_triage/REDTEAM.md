# 048_appointment_reason_triage — REDTEAM notes

## Mission
Triage tagging for upcoming visits. For every appointment on or after the episode date with status 'scheduled' or 'confirmed', add a triage_tier field: 'urgent' if the reason mentions vomiting, limping/lameness, or 'ear infection' (case-insensitive); 'routine' if it mentions wellness, vaccine, or weight management; 'standard' for everything else. Pre-episode and historical-status appointments stay untouched.

## Why this is hard / unique
Free-text keyword classification with overlapping semantics ('Ear infection re-check' urgent vs 'Vaccine boosters due' routine); agents misclassify boundary strings.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
