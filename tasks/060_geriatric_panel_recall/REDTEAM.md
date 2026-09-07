# 060_geriatric_panel_recall — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the monthly senior bloodwork recall for canine and feline patients at least 7 years old with no qualifying CBC or serum chemistry lab within the last 365 days. Produce per-patient reminder_queue rows, a summary communications row, a species-level ops_reports rollup, and an audit_log entry, all keyed by the episode batch code.

## Why this is hard / unique
- Negative-evidence join: the due set is defined by the absence of a recent lab, not by a positive flag.
- Dual-path verification: every aggregate (senior_count, recent_lab, due, recall_rate) is computed both by raw-row Python filtering and by an independent SQL query.
- Episode-date boundary sensitivity: age and recency thresholds are day-exact, but the due set must be stable across the +/-3-day episode jitter.
- Multi-collection idempotency: re-running the sweep must not duplicate reminders, summary, report rows, or audit entries.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- **Non-canine/feline senior decoys**: snapshot contains 25 non-canine/feline patients >= 7 years old (e.g., id 7 Ziggy avian, id 10 Willow equine, id 54 Penny exotic, id 31 Oliver avian, id 35 Loki equine). Verified by scanning `veterinary_clinic_system_patients` dob and species.
- **Recent-lab exclusion**: 7 canine/feline patients >= 7 years old have a qualifying CBC/chemistry lab within 365 days of the 2026-09-30 anchor (e.g., id 53 Molly canine last Serum chemistry panel 2026-01-27, id 59 Molly feline last CBC 2026-05-17, id 232 Bailey feline last CBC/chemistry 2026-07-27). Confirmed by joining `lab_results` to `patients`.
- **Name-collision hazard**: multiple due patients share names (e.g., two 'Molly' entries), so the verifier matches reminder rows by `patient_id`, not by message text.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships. Do not treat this task as done until this section is replaced with real results and `hardened_after_rounds` is recorded.
