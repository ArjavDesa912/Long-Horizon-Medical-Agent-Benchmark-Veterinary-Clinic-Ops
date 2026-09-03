# 061_new_patient_enrollment — REDTEAM notes

## Mission
Enroll a new patient: 'Maple Syrup', a female spayed rabbit (species 'exotic', breed 'Holland Lop'), born 2023-02-14, weight 1.8 kg, owned by owner id 3 (Ingrid Larsson) at location 1. Give her a valid ISO 11784 microchip id: 15 digits starting with manufacturer code 985 followed by 12 digits — use 985112 followed by zero-padded digits of 900001 (verify the ISO 11784 format online if unsure). status 'active', alerts [], spayed_neutered true, dob as an ISO timestamp at midnight UTC, created_at = episode timestamp.

## Why this is hard / unique
Microchip format requires the ISO 11784 15-digit convention; agents emit arbitrary strings without the research step.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
