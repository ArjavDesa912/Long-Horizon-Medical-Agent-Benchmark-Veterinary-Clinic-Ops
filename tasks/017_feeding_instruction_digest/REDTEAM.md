# 017_feeding_instruction_digest — REDTEAM notes

## Mission
Prepare the daily kennel care roster and provisioning digest. The roster combines in-house guests (status 'checked_in' or 'overstay') with active reserved guests (status 'reserved' and check_in <= episode_date <= check_out). It computes counts by run_type, location, and species; counts raw-diet and medicated guests; and sends one outbound email per raw-diet guest. All results land in a single ops_reports row keyed by batch_code.

## Why this is hard / unique
- Multi-source membership rule: the count depends on `status` plus an interval overlap, not a single field.
- Many breakdowns (run_type, location, species, raw_by_location, med_by_location) require cross-collection joins and are verified with dual raw-row + SQL paths.
- The 'med_guests' rule is a literal-string exclusion (the string 'None' must not count), while 'raw_diets' is a case-sensitive substring.
- The communications are keyed by (patient_id, reservation_id) to survive owner/pet-name collisions.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- At default episode 2026-09-30 the roster has 5 checked_in and 9 active reserved reservations (ids 6, 7, 17, 65, 74, 85, 98, 99, 128). Counting only one group gives the wrong total.
- Raw diets: only checked_in reservation 2 and reserved reservation 65 contain the case-sensitive substring 'Raw'.
- Med guests: 7 total; the checked_in reservation 4 and reserved reservations 6, 17, 98, 99, 128 have 'None' or null medication instructions and must be excluded.
- Species breakdown is {canine: 8, feline: 2, equine: 3, exotic: 1} at the default episode.
- Active reserved bookings 98 and 99 overlap occupied runs 4 and 3, and 74/128 are on large_dog runs; they must remain in the roster as separate guests.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
