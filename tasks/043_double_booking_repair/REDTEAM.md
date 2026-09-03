# 043_double_booking_repair — REDTEAM notes

## Mission
The schedule has double-bookings: appointments on the same date, same room, same location, and identical start_time with status 'scheduled' or 'confirmed' (completed/checked_in/no_show are history, not conflicts). For each conflicting GROUP, keep the appointment created first (earliest created_at; tie -> lowest id) and move the others: set their start_time and end_time 30 minutes later than the kept appointment's (e.g. kept 09:00–09:30 -> moved 09:30–10:00) and add field rescheduled='<batch_code>'. If the shifted slot itself collides with another same-day same-room scheduled/confirmed appointment, keep shifting by 30 minutes until free (never past 17:00 — if that would happen, instead set status 'needs_reschedule' and leave times unchanged). Do not alter kept appointments.

## Why this is hard / unique
Constraint-cascade repair (shift-until-free with a give-up state); requires simulating a deterministic algorithm — memorized answers fail after reseed.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
