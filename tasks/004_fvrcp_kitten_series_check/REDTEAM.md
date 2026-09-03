# 004_fvrcp_kitten_series_check — REDTEAM notes

## Mission
Feline patients whose FVRCP booster will come due within the next 30 days (from the episode date in ops_meta) need a head's-up before the window opens. For every feline patient with an FVRCP vaccination whose due_date falls in (episode_date, episode_date+30 days] and who has NO queued reminder yet, push one reminder_queue row with kind='vaccination_due', status='queued', queued_by='frontdesk@pawsclinic.com', due_date equal to the vaccination's due_date, and message '<PatientName> FVRCP booster due <YYYY-MM-DD> — book a nurse visit.' Finally, add a summary row with kind='compliance_summary', status='queued', and message='FVRCP due-in-30 count: <N>' where N is the number of reminder rows you created. Cats already covered by a queued vaccination_due reminder must be skipped but still counted in N as zero — i.e. N counts only rows actually created.

## Why this is hard / unique
Half-open date window + exclusion set + a self-referential summary count row; agents routinely miscount or include excluded patients.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
