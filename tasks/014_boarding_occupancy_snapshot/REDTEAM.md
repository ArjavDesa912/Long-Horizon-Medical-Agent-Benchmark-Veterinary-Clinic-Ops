# REDTEAM — 014_boarding_occupancy_snapshot

## Status

Phase 4 hardening is **pending**. This file is a stub written during the v2
hardmode codegen session; no live attack-fix-attack cycle has been run.

## Known red-herring hazards (confirmed from seed snapshot)

1. Locations 2 and 3 each have runs but zero occupied runs. The report must
   list them explicitly with `occupied: 0`; omitting them is a failure mode.
2. The five occupied runs are all `run_type = kennel`, but one guest is
   `species = feline` (patient 8) and one is `species = equine` (patient 10).
   `by_species` must come from `patients.species`, not from the run type.
3. The snapshot must aggregate `boarding_runs`, not `boarding_reservations`.
   Counting reservations would still yield five, but it would miss run-type,
   status, and location data and could count reserved decoys.
4. Fee schedule lookup is required for `board_night_rate` and
   `potential_revenue`; a shortcut that hardcodes 38 would pass on this seed
   but fail if fees change.

## Phase 4 work remaining

- Run `gold.py` and `gold_alt.py` against a live container.
- Run the verifier and confirm all dual-path counts.
- Attempt reward-hacking shortcuts:
  - write the report from reservations instead of runs;
  - drop empty locations from the report;
  - derive `by_species` from `boarding_runs.run_type`;
  - hardcode the BOARD-NIGHT rate;
  - append a new report row on each run instead of overwriting;
  - modify a run/reservation to inflate occupancy.
- Harden the verifier against each shortcut and re-run.
- Measure `max_steps` and `par_steps` from a successful live gold run and
  update `task.json`.
