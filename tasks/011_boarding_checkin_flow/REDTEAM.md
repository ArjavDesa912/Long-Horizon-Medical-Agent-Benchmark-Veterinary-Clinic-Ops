# 011_boarding_checkin_flow — REDTEAM notes (Phase 4 PENDING)

## Mission
Process the morning boarding arrivals. Check in every reserved reservation with check_in <= episode date whose assigned run is currently available, in ascending check_in order (ties by id). For each successful check-in, set the reservation to `checked_in`, the run to `occupied` with the correct patient, send the owner an email, and record a check-in manifest in `ops_reports`.

## Why this is hard / unique
- Multi-reservation arrival manifest with first-come-first-served run availability, not a single fixed reservation.
- Run-conflict hazard: two reservations can point to the same run; the earlier one must win, the later must stay reserved.
- Episode-date sensitivity changes which reservations are eligible.
- Dual-path verification of the processed set and the manifest counts.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Run-availability decoys**: among the 10 reserved reservations with `check_in <= 2026-09-30`, reservation 98 (run 4), reservation 99 (run 3), and the later pair members 17 and 6 point to runs that are unavailable or taken by an earlier guest. A solution that ignores run availability will overbook and fail.
- **Episode-date sensitivity**: at jitter -3 (`2026-09-27`) only 8 reservations are candidates and 5 are checked in; at the base and jitter +3 dates 10 are candidates and 6 are checked in.
- **Tie-breaking and run conflicts**: reservations 85 and 17 both share cattery run 10; 65 and 6 share kennel run 6. Only 85 and 65 (earlier by check_in, and by id within the same-date pair) check in.
- **Communication and manifest deduplication**: a second run must not send duplicate emails or duplicate the manifest row. Matching by subject and `patient_id` closes the duplicate hole.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
