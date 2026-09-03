# 087_template_deprecation_migration — REDTEAM notes

## Mission
The SMS channel for vaccination reminders is being retired in favor of email. Update the reminder_templates row named 'Vaccination overdue (SMS)': set channel 'email', set active false, and append to its message_template the suffix ' (migrated from SMS <batch_code>)'. All other templates stay byte-identical.

## Why this is hard / unique
String-append migration (not replacement) on a template with a nonce marker; exactness of the suffix string.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
