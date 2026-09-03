# 060_geriatric_panel_recall — REDTEAM notes

## Mission
Geriatric screening recall: dogs and cats aged 7 years or older (as of the episode date, computed from dob) who have NOT had a 'CBC' or 'Serum chemistry panel' lab result in the last 365 days are due for senior bloodwork (standard senior-wellness practice — verify if unsure). For each due patient push one reminder_queue row {kind: 'senior_lab_recall', patient_id, owner_id: <patient's owner>, message: '<PatientName> (age <age in whole years>) is due for senior bloodwork — CBC + chemistry.', status: 'queued', queued_by: 'system', queued_at: episode timestamp, due_date: episode date}. Then push ONE communications summary row to owner of the clinic (owner_id '1'): {channel: 'email', direction: 'outbound', subject: 'Senior recall batch <batch_code>', body: '<N> senior patients recalled for bloodwork.', logged_by: 'system', occurred_at: episode timestamp}. Seeded rows untouched.

## Why this is hard / unique
Age derivation from dob + negative-evidence join (no recent lab) + summary-count consistency; three ways to be subtly wrong.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
