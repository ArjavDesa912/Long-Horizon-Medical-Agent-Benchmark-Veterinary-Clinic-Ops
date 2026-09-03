# 068_patient_species_weight_sanity — REDTEAM notes

## Mission
Sanity-check patient weights against species-typical ranges (verify typical ranges online if unsure): canine 1–90 kg, feline 1–15 kg, avian 0.02–2 kg, exotic 0.02–15 kg, equine 200–700 kg, other 0.02–200 kg. For every patient whose weight_kg falls outside its species range, set weight_flag='out_of_range' and weight_checked='<batch_code>'; for every in-range patient set weight_flag='plausible' (no tag field). Patients with missing weight get weight_flag='missing'. All other fields byte-identical.

## Why this is hard / unique
Domain-range table (must be applied exactly) + three-way classification with tag-on-one-class-only asymmetry.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
