# 051_critical_lab_callback — REDTEAM notes (Phase 4 PENDING)

## Mission
Close the loop on critical lab results under the episode batch code. For every
lab_results row with flag='critical': (a) ensure a documenting communications row
exists — channel='phone', direction='outbound', subject='URGENT lab result —
<PatientName>', body='<test_name>: <result_summary>' copied exactly, logged_by
'Dr. Alvarez', occurred_at on the episode date, patient_id + owner_id set — created
only if that exact documentation is absent; (b) ensure one reminder_queue audit
marker for this batch {kind:'lab_callback', status:'done', message:'lab callback
<batch_code> verified for lab_result <id>', ...}; (c) rewrite ops_reports
'lab_flag_audit' rows for this batch — one per flag value with total and
callbacks_documented. Nothing else changes.

## Why this is hard / unique
- Per-lab documentation matching, not per-patient: the seed plants an abnormal
  row on the same patient as the only critical row, so 'any URGENT comm for this
  patient' is wrong.
- Three write surfaces (communications, reminder_queue, ops_reports) with
  byte-identical preservation of all seeded rows in the shared collections.
- Dual-path verification: per-flag totals and callbacks_documented are computed
  via raw-row Python joins AND independent SQL aggregation, three-way agreement
  required.
- Idempotent: documentation keyed on exact (patient_id, subject, body), markers
  on exact message, report deleted-then-rewritten per batch_code.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- lab_results id=1 is the only flag='critical' row (patient 4 'Noodle',
  owner_id 2); id=6 is flag='abnormal' on the SAME patient 4 — patient-level
  matching corrupts the per-lab check.
- lab_results id=42 is another 'Serum chemistry panel' but flag='normal'
  (patient 59) — a test-name match fabricates a second critical.
- lab_results id=7 is 'abnormal' on patient 27 (transferred) — out of scope.
- Seeded reminder_queue ids 1-4 (vaccination_due x2, invoice_overdue,
  boarding_checkin) must stay byte-identical beside the new lab_callback/done
  markers.
- 10 'abnormal' + 31 'normal' rows produce zero comms/markers; over-broad flag
  matching is caught by the new-row identity check and the flag-level audit.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.

### Live-QC assumptions to verify
- The SQL join `p.id::text = l.patient_id::text` and the string-concat
  `l.test_name || ': ' || l.result_summary` work through Stackhouse's
  /v1/sql/query passthrough (Postgres syntax; consistent with the reference
  task's verified SQL usage). If the endpoint rejects joins/casts, the QC
  session should swap in an equivalent independent SQL formulation.
- `patient_id` on new communications rows is checked via REST only.
- Real gold step counts still need measuring; par_steps/max_steps are null in
  task.json by design.
