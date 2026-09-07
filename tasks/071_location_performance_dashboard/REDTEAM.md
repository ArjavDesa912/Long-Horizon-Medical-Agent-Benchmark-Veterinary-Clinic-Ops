# 071_location_performance_dashboard — REDTEAM notes (Phase 4 PENDING)

## Mission
Build the monthly org-admin All Locations dashboard in `ops_reports`: per-location rollup (appointments, patients, providers, boarding occupancy, paid revenue, transfer volume) plus a per-location top paid service row.

## Why this is hard / unique
- Joins six live collections (locations, appointments, patients, providers, boarding_runs, billing_invoices, location_transfers) for a single dashboard.
- Provider home location is deliberately not the appointment location for 364 appointments; the agent must use `appointments.location_id`.
- Occupancy must come from the physical `boarding_runs` table, not `boarding_reservations`.
- `appointments_today` is episode-date dependent and jitters per episode.
- Dual-path verification on every numeric aggregate (Python + SQL).

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- 364 appointments have provider home location != appointment location (e.g. appointment id=1 is at loc 1 with provider_id=3 whose home is loc 2).
- `boarding_reservations` has 5 checked_in rows at loc 1, but the physical `boarding_runs` occupancy at loc 1 is 5/8 (62.5%), loc 2 and loc 3 are 0%.
- Top services per location are Ear cytology (loc 1, 33), Vaccination – rabies (loc 2, 37), Boarding (3 nights) (loc 3, 35).
- `patients.status='active'` filters out patient id=27 (transferred).
- Paid revenue totals: loc 1 42374.00, loc 2 35629.00, loc 3 40677.00.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
