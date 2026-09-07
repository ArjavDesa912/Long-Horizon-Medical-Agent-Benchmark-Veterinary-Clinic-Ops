# 073_provider_location_coverage — REDTEAM notes (Phase 4 PENDING)

## Mission
Produce the provider coverage (per home location) and provider workload (per appointment assignment) report for the org-admin staffing review.

## Why this is hard / unique
- Explicitly decouples provider home location from where appointments happen (364 cross-booked appointments).
- Support staff (vet_tech, kennel_attendant, groomer) have zero appointments but must be reported.
- Adds per-location `patients_per_veterinarian` ratio, `has_kennel_staff` boolean, and boarding run occupancy to the coverage view.
- Dual-path verification on all appointment and patient counts.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- 364 appointments have provider home location != appointment location.
- Support staff providers id=5, 6, 7, 8, 9 have zero appointments.
- Location 2 has no `kennel_attendant` (Lucy Tran is a groomer), so `has_kennel_staff` is false for loc 2 only.
- Active patients per location: loc 1 100, loc 2 106, loc 3 93; veterinarians: loc 1 2, loc 2 1, loc 3 1.
- Per-location appointment status counts differ (loc 1 187 total/58 completed/27 no_show, loc 2 181/58/20, loc 3 180/60/19).

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
