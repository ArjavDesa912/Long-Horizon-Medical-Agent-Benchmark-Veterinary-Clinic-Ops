# 059_species_visit_mix_report — REDTEAM notes (Phase 4 PENDING)

## Mission
Produce the Visits by Species report for this episode. Write a species rollup with visits, distinct patients, pct_of_visits, and pct_of_patients, plus a species-by-location matrix. All counts must be derived from a live join of `visit_records` and `patients`.

## Why this is hard / unique
- Two-level aggregation (species and species+location) from a join.
- `pct_of_patients` uses the full `patients` table (300) as the denominator, not just patients with visits.
- Multiple visits per patient must be counted as visits.
- Zero-visit species must be absent, not written as zero rows.
- Dual-path verification (Python join vs SQL GROUP BY).
- Delete-then-rewrite idempotency per batch.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `pct_of_patients` denominator is 300 (all `patients` rows), not 202 (the sum of distinct patients with visits: avian 18 + canine 99 + equine 10 + exotic 12 + feline 63 = 202).
- Patient 216 has two `visit_records` (id=10 and id=12); both are canine and must each count as a visit.
- `visit_records` id=371 is unlocked and incomplete but is still a canine visit (patient 5) and must count.
- Only five species appear in visits; rows for any other species must be absent.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
