# 083_file_storage_audit — REDTEAM notes (Phase 4 PENDING)

## Mission
Audit the `files` collection: produce a per-bucket storage summary (count, bytes, MB, doc_types, content_types) and a path-compliance report listing any file whose path is missing the `<patient_id>/` prefix. Do not modify `files`.

## Why this is hard / unique
- Bucket-level aggregation with exact MB rounding using 1048576 (not 1000000).
- Sorted distinct CSV strings for doc_types and content_types.
- Path-convention compliance must be derived per row without modifying the source.
- SQL dual-path on both summary and exception list.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Only `files` id 2 (patient_id '4', path '2026-05-02/hip-ventrodorsal.png') is missing the `<patient_id>/` prefix; all other 7 files are prefix-compliant.
- `files` id 3 has a date second segment and a filename typo but is compliant (path starts with patient_id '10').
- Bucket totals: vet-imaging 4 files, 560328 bytes, 0.53 MB; vet-documents 4 files, 163420 bytes, 0.16 MB.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks before this task ships.
