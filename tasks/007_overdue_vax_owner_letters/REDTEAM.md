# 007_overdue_vax_owner_letters — REDTEAM notes

## Mission
Monthly compliance sweep, batched under the episode batch code. (1) In reminder_queue, mark every currently-queued vaccination_due row as status='sent' with sent_on set to the episode date. (2) For every patient that still has at least one overdue vaccination as of the episode date (due_date strictly before the episode date) — whether or not it had a queued reminder — push one communications row to its owner: channel='email', direction='outbound', subject='Vaccination compliance notice <batch_code>' (batch code from ops_meta), body='<PatientName> has <K> overdue vaccination(s) as of <episode date YYYY-MM-DD>.', logged_by='system', occurred_at on the episode date. (3) Push one audit-style row into reminder_queue: kind='sweep', status='done', message='sweep <batch_code>: <R> reminders sent, <C> owner notices', where R is the number of rows flipped in step 1 and C the number of rows created in step 2. Seeded communications must remain untouched.

## Why this is hard / unique
Three-phase batch with cross-collection count consistency (sweep row must agree with actual mutations) and nonce-stamped subjects — memorized counts fail on reseed.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
