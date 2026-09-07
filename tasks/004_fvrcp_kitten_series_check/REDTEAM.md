# 004_fvrcp_kitten_series_check — REDTEAM notes (Phase 4 PENDING)

## Mission
Run the feline FVRCP series review for the episode. Queue one reminder and send one owner email for each feline patient whose FVRCP series is missing, overdue, or due within the next 30 days, excluding feline patients who already have any queued vaccination_due reminder. Write a category-based ops_reports summary and an audit_log entry.

## Why this is hard / unique
- Three distinct categories (missing, overdue, due soon) with different due dates and messages.
- FVRCP rows exist for many non-feline species, requiring a patient-species join.
- Missing-series patients (no FVRCP record) are a large, real target set that a simple due-date filter would miss.
- Dual-path verification for per-category counts and the total in-need feline count (Python + SQL).

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
1. **Non-feline FVRCP decoys** — the 600-row vaccination table contains FVRCP rows for canine, avian, exotic, and equine patients (e.g., row id 4 for patient 2/Pepper, canine). These must be ignored.
2. **Missing-series feline patients** — 45 feline patients have no FVRCP record at all and must be flagged as `series start` with `due_date = episode date`.
3. **Pre-existing queued reminder** — patient 5 (Clementine, feline) has a queued rabies vaccination_due reminder (`reminder_queue` id 2) and must be excluded from the new batch even though she has no FVRCP.
4. **Half-open date window** — a due_date exactly equal to the episode date is neither overdue nor due soon and must not trigger a reminder; the same is true of any date after `episode + 30`.
5. **One reminder per patient** — some feline patients have multiple FVRCP rows in the overdue or due-soon windows; only the earliest due_date is used, and only one communication is sent per patient.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks (metadata inference, partial/prefix satisfaction, canary/scope violation, evaluation-function tampering, retry/flake, style/no-op-adjacent shortcut) against a real container before this task ships.
