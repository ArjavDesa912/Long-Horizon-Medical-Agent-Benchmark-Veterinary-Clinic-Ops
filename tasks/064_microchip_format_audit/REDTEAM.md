# 064_microchip_format_audit — REDTEAM notes (Phase 4 PENDING)

## Mission
Audit every patient's microchip against ISO 11784 (15 decimal digits). Flag all non-compliant patients, enqueue one microchip recall reminder per affected patient, produce species-level and ALL rollup compliance reports, and append a MICROCHIP_AUDIT audit and communications summary.

## Why this is hard / unique
- Bulk fleet audit: all 300 patients in the snapshot fail the 15-digit rule, so the agent must correctly update 300 rows and enqueue 300 reminders.
- Do-not-invent constraint: the agent must only write `microchip_flag`/`microchip_flagged`, never generate a new `microchip_id` for an existing patient.
- Multi-collection artifact set: patients, reminder_queue, ops_reports, audit_log, and communications.
- Dual-path verification: the non-compliant set and species counts are recomputed with Python regex and SQL regex.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **All-300 non-compliant**: 299 patients have exactly 12-digit microchips (e.g., patient 1 '985112100000'); patient 30 has an 11-digit microchip '98511232965'. Confirmed by scanning `veterinary_clinic_system_patients`.
- **Species distribution**: the non-compliant set spans all five species (canine 153, feline 90, avian 21, exotic 20, equine 16). Confirmed from `veterinary_clinic_system_patients`.
- **Transferred-status decoy**: patient 27 (Poppy, feline, status 'transferred') is still active in the database and must be audited/flagged. Confirmed from the snapshot.
- **Do-not-invent**: no patient currently has a 15-digit microchip; the only compliant chip is the one the agent creates for the new-patient task (if run), not here.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
