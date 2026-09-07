# 084_imaging_metadata_gap_fill — REDTEAM notes (Phase 4 PENDING)

## Mission
Repair file metadata in `files`: ensure every path starts with `<patient_id>/`, set `doc_type` by bucket convention (`vet-imaging` by filename extension, `vet-documents` by second path segment), tag repaired rows, append `audit_log` entries, and write an `ops_reports` summary.

## Why this is hard / unique
- Multi-collection repair with an audit trail.
- Bucket-specific doc_type rules (extension for imaging, path segment for documents).
- Only the genuinely broken rows should change; compliant rows must stay byte-identical.
- Requires an audit_log entry with exact action/details per repaired file.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Only `files` id 2 is missing the `<patient_id>/` prefix (patient_id '4', path '2026-05-02/hip-ventrodorsal.png').
- `vet-imaging` ids 1 and 2 are `.png` -> 'radiograph'; ids 3 and 7 are `.jpg` -> 'clinical photo'.
- `vet-documents` ids 4-8 have doc_type equal to the second path segment.
- Compliant rows must not receive `path_fixed`/`metadata_repaired` tags; only repaired rows do.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks before this task ships.
