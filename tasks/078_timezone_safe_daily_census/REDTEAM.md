# 078_timezone_safe_daily_census — REDTEAM notes

## Mission
All three clinics operate in the America/New_York timezone (see the locations collection). Using that timezone (verify its UTC offset handling if unsure), compute the daily census: for the EPISODE DATE as seen in America/New_York, one ops_reports row {report: 'daily_census', batch_code, census_date: '<YYYY-MM-DD in ET>', appointments_that_day: <appointments whose appointment_date equals it>, boarding_guests_that_day: <checked_in reservations whose stay covers it (check_in <= date <= check_out)>, new_invoices_that_day: <invoices issued that day>}.

## Why this is hard / unique
Timezone conversion (UTC episode instant -> ET calendar date) before date equality — agents compare in UTC and miss boundary rows.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
