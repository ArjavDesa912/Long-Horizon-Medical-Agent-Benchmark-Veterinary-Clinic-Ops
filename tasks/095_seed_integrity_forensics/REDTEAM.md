# 095_seed_integrity_forensics — REDTEAM notes (Phase 4 PENDING)

## Mission
Run a read-only forensic audit across the whole seeded dataset and produce a single `ops_reports` row summarizing five integrity rules: provider/appointment location alignment, species-appropriate vaccines, duplicate owner phones, dangling foreign keys, and negative owner balances.

## Why this is hard / unique
- The audit spans 10+ collections and derives business rules (FVRCP=feline, DHPP/bordetella=canine, provider primary location) from domain standards rather than being stated in the instruction.
- Every rule is recomputed two independent ways (raw-row Python filter and SQL SELECT/COUNT) and must agree with the written report.
- The seed contains a large number of real-looking anomalies (364 provider/location mismatches, 161 vaccine/species mismatches) plus carefully placed clean rules (zero dangling references) that force the agent to actually run the checks instead of assuming a total.
- The report is idempotent: re-running produces byte-identical state because prior rows for the batch are deleted before the new report is pushed.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- `provider_location_mismatch`: 364 appointments violate the rule. Row-level evidence: appointment id 1 has `provider_id` 3 (provider 3 `location_id` is 2) but `location_id` 1; id 2 has provider 1 (`location_id` 1) at location 2; etc.
- `vaccine_species_mismatch`: 161 vaccination rows. Row-level evidence: vaccination id 4 (`patient_id` 2, species canine) has `vaccine_type` `FVRCP`; id 6 (`patient_id` 3, species feline) has `vaccine_type` `bordetella`; full list ids 4,6,10,12,15,21,23,29,31,42,...
- `duplicate_owner_phone`: owners id 1 (Margaret Whitfield) and id 22 (Faye Lovelace) both have phone `(828) 555-0101` (confirmed in owners rows at snapshot lines ~24478 and ~24792).
- `negative_owner_balance`: owner id 21 (eugene.kim@example.com) has `balance` `-45.0` (snapshot line ~24775). All other 219 owners have `balance >= 0`.
- `controlled_substance_log` null `patient_id` rows: ids 3,5,8,10 have `patient_id` null for actions `waste`/`receive`; a naive FK check must not count nulls as violations (the verifier allows null for all actions).

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
