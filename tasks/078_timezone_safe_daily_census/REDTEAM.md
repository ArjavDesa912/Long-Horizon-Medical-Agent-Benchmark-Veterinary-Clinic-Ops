# 078_timezone_safe_daily_census — REDTEAM notes (Phase 4 PENDING)

## Mission
Compute the daily clinic census for the America/New_York calendar date of the episode. The result is one `ops_reports` row that records both the timezone-safe count (convert each stored UTC timestamp to America/New_York and count what falls on the ET census date) and the naive count (compare the raw stored 10-character date prefix to the ET census date), for scheduled/confirmed appointments, checked-in boarding guests, and new invoices.

## Why this is hard / unique
- **ZoneInfo conversion is required**: the episode is a UTC midnight timestamp and the locations are in America/New_York (EDT in late September), so the ET census date is always the previous calendar day. A fixed `-4` guess happens to be right but is not general; `America/New_York` follows DST rules.
- **Dual counts expose the day shift**: the agent must produce both the correct ET count and the wrong naive count in the same row, which makes a pure raw-prefix solution fail.
- **Zero-count traps**: for the 2026-09-27..2026-10-02 episode window, no checked_in boarding reservations and no invoices fall on the ET census date, so an overbroad `SELECT *` or a count of all checked_in rows overreports.
- **Dual-path verification**: the verifier recomputes every number both via raw-row Python/zoneinfo and SQL UTC-bound queries and the two must agree.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Day shift on 2026-09-30**. Snapshot `veterinary_clinic_system_appointments` raw date `2026-09-29` has 10 scheduled + 4 confirmed rows; raw `2026-09-30` has 13 scheduled + 6 confirmed rows. Because `2026-09-30T00:00:00Z == 2026-09-29 20:00 EDT`, the ET census date for episode 2026-09-30 is 2026-09-29 and the correct ET count is 13 scheduled + 6 confirmed. The naive count for 2026-09-29 (raw prefix 2026-09-29) is 10 scheduled + 4 confirmed. Row samples: id 66 raw 2026-09-29 -> ET 2026-09-28; id 69 raw 2026-09-30 -> ET 2026-09-29.
2. **All locations are America/New_York**. Snapshot `veterinary_clinic_system_locations` rows id 1 (Main Street Animal Hospital, Asheville NC), id 2 (Riverside Veterinary Clinic, Greenville SC) and id 3 (Cedar Park Animal Care Center, Knoxville TN) all have `timezone: "America/New_York"`.
3. **Zero boarding guests**. The only `checked_in` reservations are ids 1-5 with `check_out` on or before 2026-09-09 (id 1 check_in 2026-09-03 check_out 2026-09-09, id 5 check_in 2026-09-01 check_out 2026-09-07), all before the episode window.
4. **Zero new invoices**. The newest `issued_date` in `veterinary_clinic_system_billing_invoices` is id 3 with `2026-09-02T00:00:00+00:00`; all others are earlier, so no invoice falls on any ET census date in the 2026-09-27..2026-10-02 window.
5. **Status and format filters**. `veterinary_clinic_system_appointments` contains 66 `no_show`, 176 `completed`, 10 `checked_in`, 205 `scheduled` and 91 `confirmed` rows. Only `scheduled` and `confirmed` count. Dates are stored as `2026-09-30T00:00:00+00:00`; bare date strings persist as NULL in this Stackhouse build.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
