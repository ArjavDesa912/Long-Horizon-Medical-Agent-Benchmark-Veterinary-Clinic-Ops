# 079_appointment_to_visit_linkage — REDTEAM notes

## Mission
Measure clinical follow-through: what fraction of completed appointments have a matching visit record (same patient, same provider, visit_date equal to the appointment_date)? One ops_reports row {report: 'follow_through', batch_code, completed_appointments, matched: <completed appointments with an exact 3-field match in visit_records>, unmatched, match_pct: <round(100*matched/completed,1)>, unmatched_ids: <comma-joined ascending ids of unmatched completed appointments, or ''>}.

## Why this is hard / unique
Three-field join predicate with an id-listing requirement; partial matches (patient-only) are the classic overcount.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
