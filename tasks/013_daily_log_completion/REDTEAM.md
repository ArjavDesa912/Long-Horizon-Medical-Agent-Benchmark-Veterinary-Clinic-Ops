# REDTEAM — 013_daily_log_completion

## Status

Phase 4 hardening is **pending**. This file is a stub written during the v2
hardmode codegen session; no live attack-fix-attack cycle has been run.

## Known red-herring hazards (confirmed from seed snapshot)

1. Medication-instruction red herring: four of the five `checked_in`
   reservations have non-"None" `medication_instructions`, but none of those
   five patients has an `active = true` record in `medications`.
2. Species vs. run-type red herring: `patient_id 10` is `species = equine`
   but is assigned to a `run_type = kennel` run, so `walked` must be true
   under the run-type rule.
3. Existing `boarding_daily_log` rows for 2026-09-03/04 must remain
   byte-identical; the task only creates/updates the episode-date row.

## Phase 4 work remaining

- Run `gold.py` and `gold_alt.py` against a live container.
- Run the verifier; confirm dual-path SQL/Python totals and canaries.
- Attempt reward-hacking shortcuts:
  - mark every log `medicated = true` because instructions exist;
  - set `walked` from `patients.species` instead of `boarding_runs.run_type`;
  - upsert by inserting duplicate rows instead of update-by-key;
  - modify `boarding_reservations` or `boarding_runs` to fake more guests.
- Harden the verifier against each shortcut and re-run.
- Measure `max_steps` and `par_steps` from a successful live gold run and
  update `task.json`.
