# 096_temporal_anomaly_detection — REDTEAM notes

## Mission
READ-ONLY anomaly hunt — mutate nothing. Find temporal impossibilities across the dataset: (a) vaccinations with due_date before administered_date; (b) boarding_reservations with check_out before check_in; (c) billing_invoices with due_date before issued_date; (d) billing_estimates with expires_date before created_date; (e) visit_records with locked_at before visit_date; (f) appointments whose end_time is not after start_time. Report one ops_reports row {report: 'temporal_anomalies', batch_code, anomalies: <total>, by_rule: <JSON object rule name ('vaccination_due_before_admin','stay_backwards','invoice_due_before_issued','estimate_backwards','lock_before_visit','appointment_time_inversion') -> count>, row_refs: <comma-joined ascending '<collection_short>:<id>' list of every offending row, or ''>}.

## Why this is hard / unique
Six heterogeneous temporal predicates including a same-day time-string comparison; agents typically miss the lock-vs-visit and time-inversion rules.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
