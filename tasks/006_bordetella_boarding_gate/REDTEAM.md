# 006_bordetella_boarding_gate — REDTEAM notes

## Mission
Run the boarding bordetella gate for the episode. A dog may not check in for boarding unless its bordetella vaccination stays current through the end of the stay. For every boarding reservation with status in ('reserved','checked_in') whose patient is canine and whose latest bordetella due_date is on or before the reservation's check_out date, OR whose patient has no bordetella record at all, update the reservation to `status='waitlisted_vax'` and `hold_reason='bordetella lapse before checkout'`. Notify the owner by email and write an ops report and audit log.

## Why this is hard / unique
- Real kennel rule (vaccine must cover the whole stay, not just the episode date).
- Missing bordetella record is treated as lapsed, not ignored.
- Multi-status filter (`reserved` + `checked_in`) rather than only `reserved`.
- Date comparison is against `check_out`, not `check_in` or the episode date.
- Owner communications, ops report, and audit log are added to the original v1 scope.
- All aggregates are verified by dual Python/SQL paths.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Both `reserved` and `checked_in` reservations are gated** — the two checked-in canine reservations (ids 1 and 3) are real targets.
2. **Non-canine reservations are not gated** — feline, avian, exotic, and equine patients must retain their original status.
3. **Missing bordetella = lapsed** — some canine patients have no bordetella row at all and must be waitlisted.
4. **Check-out date comparison** — reservation 76 (patient 52, Bordetella due 2026-11-14, checkout 2026-11-23) is a canonical lapsed case; comparing against `check_in` or the episode date would change the target set.
5. **Field preservation** — only `status` and `hold_reason` may change; every other reservation field must remain byte-identical to seed.
6. **One communication per target reservation** — keyed by (subject, patient_id, body); multi-pet owners with multiple reservations on hold must receive one per reservation.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships.
