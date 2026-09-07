# 067_multi_pet_household_report - REDTEAM notes (Phase 4 PENDING)

## Mission
For every owner with 2+ active patients, push an ops_reports `multi_pet_household` row with owner name, pet count, sorted species mix, primary location, and overdue-vax count. For every such household with overdue vax, enqueue a `multi_pet_vax_recall` reminder and write an audit log entry.

## Why this is hard / unique
- Cross-collection aggregation over patients, owners, and vaccinations with 10x volume.
- Active-pet filter; transferred/deceased patients must be excluded.
- Species_mix is a sorted set; primary location is a mode with tie-breaking by lowest id.
- Overdue vax count is a join, not a simple filter, and must be done per distinct patient.
- Dual-path verification (Python vs SQL GROUP BY).

## Hazards planted (task.json.hazards) - confirmed against seed_snapshot.json
- Owner 3 has active feline 5, active avian 248, and transferred feline 27.
- 8 multi-pet owners have two active pets with the same name (owner 2 has two 'Cooper' canines, etc.).
- Some households are single-species (owner 1 has two canines).
- 104 patients have overdue vaccinations as of 2026-09-30, across 56 multi-pet households.
- 132 owners have fewer than 2 active patients and must be excluded.

## Phase 4 - NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
