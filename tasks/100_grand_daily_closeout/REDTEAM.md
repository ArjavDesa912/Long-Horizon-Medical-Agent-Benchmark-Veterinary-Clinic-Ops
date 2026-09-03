# 100_grand_daily_closeout — REDTEAM notes

## Mission
The full end-of-day closeout the practice manager runs, batched under the episode batch code: (1) reflag invoices: 'sent' with due_date strictly before the episode date become 'overdue'; (2) flush the queue: every reminder_queue row with status 'queued' becomes 'sent' with sent_on = episode date; (3) close the boarding day: for each checked_in reservation ensure an episode-date boarding_daily_log row exists (create with all care booleans false, notes 'closeout <batch_code>', logged_by 'system' if missing; leave existing rows alone); (4) write the summary: one ops_reports row {report: 'daily_closeout', batch_code, invoices_flagged: <count changed in step 1>, reminders_sent: <count changed in step 2>, boarding_rows_created: <count created in step 3>, episode_date: '<YYYY-MM-DD>'}; (5) one audit_log row {actor: 'Dana Whitaker', actor_role: 'org_admin', action: 'DAILY_CLOSEOUT', target_collection: 'ops_reports', target_id: 'daily_closeout', details: 'Closeout <batch_code>: <invoices_flagged>i/<reminders_sent>r/<boarding_rows_created>b', occurred_at: episode timestamp}.

## Why this is hard / unique
Five-phase composite where the summary/audit rows must agree with the actual mutations (self-consistency), plus idempotent boarding upsert — the capstone.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
