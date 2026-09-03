# 062_transfer_approval_flow — REDTEAM notes

## Mission
Process the transfer queue the way the Locations → Transfers screen does. For every location_transfers row with status 'pending' whose note does NOT contain the word 'Specialist' (specialist referrals stay pending for the medical director): set status 'completed', completed_at = episode timestamp; rewrite the patient's location_id to the transfer's to_location_id; and append one audit_log row {actor: 'Dana Whitaker', actor_role: 'org_admin', action: 'TRANSFER_COMPLETED', target_collection: 'patients', target_id: <patient id as string>, details: 'Transfer completed <batch_code>: loc <from> -> loc <to>.', occurred_at: episode timestamp}. The already-'approved' transfer is out of scope for this queue and stays untouched.

## Why this is hard / unique
Three-collection cascade with a text-based exclusion ('Specialist' notes) and an out-of-scope decoy status ('approved').

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
