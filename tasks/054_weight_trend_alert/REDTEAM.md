# 054_weight_trend_alert — REDTEAM notes

## Mission
Flag unhealthy weight trends. For every patient with at least 2 visit_records, compare weight_kg at the most recent visit vs the earliest recorded visit: a gain or loss of more than 10% (strictly) is clinically significant (verify the rule of thumb if unsure). For each flagged patient: (1) add the alert string 'Weight change >10% — review diet plan' to the patient's alerts array (append; preserve existing alerts; skip patients already carrying this exact alert); (2) push one ops_reports row {report: 'weight_alert', batch_code, patient_id, name, first_weight, latest_weight, change_pct: <round(100*(latest-first)/first, 1)>, direction: 'gain' or 'loss'}. Patients with fewer than 2 visits are ignored.

## Why this is hard / unique
Temporal first-vs-last comparison with strict threshold, array-append semantics, and duplicate-suppression — a 3-way skill check.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
