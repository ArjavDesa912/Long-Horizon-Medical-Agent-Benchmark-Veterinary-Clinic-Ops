# 009_rabies_certificate_doc_check — REDTEAM notes

## Mission
State rule of thumb: every dog with a current (not overdue) rabies vaccination should have a rabies certificate on file. In the files collection, add field doc_status to every files row with doc_type='rabies-certificate': 'current' if that file's patient has a rabies vaccination with due_date on or after the episode date, else 'stale'. Then, for each canine patient whose rabies is current but who has NO rabies-certificate file row, push one placeholder row: {bucket: 'vet-documents', path: '<patient_id>/rabies-certificate/pending-<batch_code>.pdf', patient_id, doc_type: 'rabies-certificate', filename: 'pending-<batch_code>.pdf', content_type: 'application/pdf', size_bytes: 0, uploaded_by: 'system', uploaded_at: <episode timestamp>, doc_status: 'current'}. Do not modify other files rows beyond the doc_status addition, and do not touch non-certificate rows at all.

## Why this is hard / unique
Two-way reconciliation (annotate existing + synthesize missing) driven by a join across three collections; placeholder naming embeds the live nonce.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
