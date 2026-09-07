# 068_patient_species_weight_sanity - REDTEAM notes (Phase 4 PENDING)

## Mission
Run a species/weight sanity audit on the patients table using web-search-derived species-typical weight ranges. Set weight_flag to plausible/out_of_range/missing, tag out_of_range rows with weight_checked=batch, write a per-species + ALL weight_sanity ops_reports summary, enqueue a weight_recheck reminder for every out_of_range patient, and write an audit log.

## Why this is hard / unique
- The exact species ranges must be recovered from current veterinary references, not given in the prompt.
- Per-patient flag updates across 300 patients with tag-on-only-one-class asymmetry.
- Boundary hazards: avian weights at 1.0, small canines at 4-5 kg, equine at 398 kg.
- Dual-path verification: Python filter vs SQL GROUP BY/CASE counts.
- Idempotent re-run: same flags, report, reminders, and audit state.

## Hazards planted (task.json.hazards) - confirmed against seed_snapshot.json
- All 21 avian patients have weight_kg = 1.0 (ids 7, 23, 31, 38, 95, 100, 106, 112, 135, 150, etc.).
- 7 small canines at 4-5 kg (ids 66, 144, 146, 166, 201, 205, 264).
- 16 equine patients range 398-518 kg; id 211 is 398 kg.
- All 300 patients have non-null weight_kg.

## Phase 4 - NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
