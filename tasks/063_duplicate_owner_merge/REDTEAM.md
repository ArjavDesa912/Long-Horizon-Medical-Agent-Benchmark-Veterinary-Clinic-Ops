# 063_duplicate_owner_merge — REDTEAM notes

## Mission
Merge duplicate owner records the way the Owners screen's merge tool should. Two owners are duplicates iff their normalized phone numbers match (digits only) OR their emails match case-insensitively. For each duplicate PAIR in the seeded data: keep the record with the earlier created_at (the survivor), repoint all patients, invoices, and communications from the duplicate to the survivor, add the duplicate's balance to the survivor's, then delete the duplicate owner row and add merged_into='<survivor id>' audit trail by pushing one audit_log row {actor: 'Dana Whitaker', actor_role: 'org_admin', action: 'OWNER_MERGE', target_collection: 'owners', target_id: <deleted owner id as string>, details: 'Merged into owner <survivor id> (<batch_code>)', occurred_at: episode timestamp}. If no duplicates exist, change nothing.

## Why this is hard / unique
Entity resolution with normalization rules + multi-collection foreign-key repointing + balance conservation; the hardest CRUD skill set.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
