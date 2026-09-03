# 002_rabies_booster_due_recompute — REDTEAM notes

## Mission
A data-import glitch wiped the due dates on all rabies vaccinations for canine patients. Recompute and set the due_date for every rabies vaccination belonging to a canine patient as exactly 1 year after its administered_date (per the AAHA canine vaccination guideline that a rabies booster follows the initial dose by 1 year — look this up if unsure). Leave feline/other-species rabies rows and every other field untouched. Write dates as ISO timestamps at midnight UTC (YYYY-MM-DDT00:00:00.000Z).

## Why this is hard / unique
Requires external guideline knowledge (AAHA 1-year rabies booster) combined with a species join; date-arithmetic edge cases (leap day) make naive hardcoding brittle.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
