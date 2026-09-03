# 026_invoice_number_gap_audit — REDTEAM notes

## Mission
Invoice numbers should be a gap-free sequence INV-1001..INV-1026. Verify and report: create one ops_reports row {report: 'invoice_sequence', batch_code, min_num: <smallest numeric suffix>, max_num: <largest>, count: <invoice rows>, missing: <comma-joined ascending list of missing numbers in that range, or ''>, sequence_ok: <true iff count == max-min+1 and there are no gaps>}.

## Why this is hard / unique
Sequence-integrity reporting (gap detection) — agents typically count rows and skip the actual gap math.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
