# RECON — veterinary_clinic_system (Phase 0 inventory)

Recon performed against a live container of `rl-env/veterinary_clinic_system:latest`
(host ports 15110/18080, container `rlrecon-vet`), 2026-08-30. Live observations
were trusted over the spec/manifest wherever they disagree.

## Source software

- Spec: `example-for-baas-main/softwares/veterinary_clinic_system/10_veterinary_clinic_system.md`
- App: `softwares/veterinary_clinic_system/veterinary_clinic_system-app` (React/Vite, port 5110)
- Seeder: `veterinary_clinic_system-app/src/scripts/seed.js` (deterministic LCG, `rngState = 42`)
- API source of truth: `softwares/veterinary_clinic_system/VIBEDB_LLM_PROMPT.md`
- Image: `rl-env/veterinary_clinic_system:latest` — Postgres 15 + VibeDB + prebuilt
  Vite dist, seeded at **build time** (`rl-env/base/seed-in-build.sh`), so
  date-relative seed values are frozen at image build time.

## Critical platform finding (seed bug — fixed, see BUILD_NOTES.md)

**VibeDB (this build) stores bare `YYYY-MM-DD` strings as `NULL`.** Verified by
probe push/readback: `{"date_only": "2026-09-15"}` reads back `null`, while any
value with a time component (`2026-09-15T00:00:00Z`, `2026-09-15 00:00:00`)
persists as a timestamptz. The seeder's `daysFromNow()` emitted date-only
strings, so in the shipped image **every business-date column was NULL**:
`appointments.appointment_date` (46/46), `vaccinations.administered_date` &
`due_date` (60/60), `billing_invoices.issued_date`/`due_date` (26/26),
`boarding_reservations.check_in/out` (14/14), `patients.dob` (30/30),
`visit_records.visit_date` (36/36), `waitlist.requested_date`, `reminder_queue.due_date`,
`boarding_daily_log.log_date`, `billing_estimates.*_date`.

Minimal fix applied to `seed.js`: `daysFromNow()` now returns
`YYYY-MM-DDT00:00:00.000Z` (midnight-anchored ISO). This keeps the app's
lexicographic date-prefix comparisons working (`due_date >= today` etc.) while
persisting correctly. **All verifiers in this env compare dates by their
10-char prefix (`vlib.dp()`), never by full-string equality.**

Intentional NULLs (not bugs): `boarding_runs.current_patient_id` (12/17 null =
available runs), `medications.dea_schedule` (null on non-controlled),
`controlled_substance_log.patient_id` (null on receive/waste),
`location_transfers.completed_at` (null unless completed), `visit_records.locked_at`
(null on unlocked notes), `reminder_queue.owner_id`/`patient_id` (kind-dependent).

## Live table inventory (24 app collections, prefix `veterinary_clinic_system_`)

| collection | rows | key fields (live shape) |
|---|---|---|
| locations | 3 | id 1/2/3, name, address{street,city,state,zip}, timezone, phone, operating_hours |
| providers | 9 | id 1–9, full_name, role (veterinarian×4, vet_tech×2, kennel_attendant×2, groomer×1), specialties[], location_id, exam_rooms[], email |
| fee_schedules | 3 | location_id, items[6]{code,description,price} — codes WELL-EXAM 62, SICK-EXAM 85, DENTAL-PROPHY 385, VACC-RABIES 28, CBC-CHEM 148, BOARD-NIGHT 38 |
| reminder_templates | 5 | name, channel(email/sms), trigger, days_offset, message_template with `{{vars}}`, active |
| owners | 22 | full_name, phone, email, address{}, balance (idx4=412.50, idx9=128.00, ~25% rand 20–180), created_at |
| patients | 30 | id 1–30; owner_id, location_id, name, species(canine 14/feline 9/avian 2/exotic 2/equine 2… see snapshot), breed, sex, spayed_neutered, dob, weight_kg, microchip_id `985112######`, alerts[], status (id 27 = transferred, rest active). Alerts: id 4 anesthetic risk, id 13 penicillin allergy, id 28 bite history |
| appointments | 46 | patient_id, provider_id, location_id, room `Exam 1–3`, appointment_date, start/end_time, reason, status (completed/no_show/scheduled/confirmed/checked_in) |
| visit_records | 36 | SOAP fields, problems[]{name,status}, weight_kg, locked_at (set when >30d old) |
| lab_results | 6 | patient_id, test_name, result_summary, flag (critical×1/abnormal×2/normal×3), resulted_at |
| vaccinations | 60 | patient_id (2 per patient), vaccine_type (rabies 15, DHPP 16, FVRCP 15, bordetella 14), administered_date, due_date, lot_number, administered_by |
| medications | 20 | 15 common + 5 controlled (buprenorphine V, tramadol IV, ketamine III, alprazolam IV); active bool, refills_remaining |
| boarding_runs | 17 | run_number K01–K08 (loc 1), C09–C13 cattery (loc 2), X14–X17 large_dog (loc 3); status available/occupied; current_patient_id |
| boarding_reservations | 14 | 5 checked_in (drives run occupancy), 3 reserved (future), 6 checked_out; feeding/medication instructions |
| boarding_daily_log | 10 | reservation_id, log_date, fed_am/fed_pm/medicated/walked bools, notes, logged_by |
| waitlist | 6 | patient_id, requested_date, reason, priority (urgent×2, work_in×2, routine×2), status waiting |
| location_transfers | 6 | 3 pending, 1 approved, 2 completed; from/to location, requested_by, note |
| pharmacy_inventory | 34 | item_name, category(medication/supply), quantity_on_hand, reorder_level, unit_price, supplier, location_id (1&2 only), 4 is_controlled items |
| controlled_substance_log | 12 | item_name, action(receive/administer/waste/dispense), quantity, witnessed_by, performed_by, occurred_at, patient_id?, notes |
| billing_invoices | 26 | INV-1001…INV-1026; idx0 OVERDUE (issued −35d, due −14d, sent), idx1 sent (−5d), idx2 draft (−2d), rest paid; line_items[{description,quantity,unit_price}], total_amount, amount_paid |
| billing_estimates | 10 | EST-3001…EST-3010; 4 sent, 2 accepted, 1 declined, 3 draft |
| communications | 16 | owner_id, channel, direction, subject, body, occurred_at, logged_by |
| reminder_queue | 4 | vaccination_due×2 (queued), invoice_overdue (sent), boarding_checkin (queued) |
| files | 8 | bucket vet-imaging/vet-documents, path, patient_id, doc_type, filename, size_bytes |
| audit_log | 4 | actor, actor_role, action, target_collection, target_id, details, occurred_at |

## Credentials (from `/rl/manifest.json` + seed)

| account | password | role |
|---|---|---|
| rl-admin@rl.local | RLVerifier2025! | uniform RL verifier (org_admin metadata) |
| admin@pawsclinic.com | Demo123! | org_admin (app_admin) |
| manager@pawsclinic.com | Demo123! | location_manager (loc 1) |
| dr.alvarez@pawsclinic.com | Demo123! | veterinarian (loc 1) |
| frontdesk@pawsclinic.com | Demo123! | front_desk (loc 1) |
| kennel@pawsclinic.com | Demo123! | kennel_staff (loc 1) |

## VibeDB endpoints the app actually uses (confirmed vs API reference)

`POST /v1/auth/login` · `POST /v1/auth/signup` · `GET /v1/auth/me` ·
`GET /v1/query/{c}` (with `?limit&offset&order_by&order_dir` + equality filters) ·
`GET /v1/query/{c}/{id}` · `POST /v1/push/{c}` · `POST /v1/update/{c}/{id}` ·
`POST /v1/delete/{c}/{id}` · `POST /v1/sql/query` (read; gated to service admins —
verifier account works) · `POST /v1/sql/execute` (write; used by the app as a
constraint re-check) · `GET/POST /v1/storage/buckets` · `GET /v1/storage/list/{b}` ·
`GET/POST /v1/rls/{c}/status|enable` · `GET /v1/admin/branches` ·
`ws://…/v1/realtime` (boarding board) · `GET /v1/tables` · `GET /health`

Mutations use `POST` verbs only — VibeDB 404s plain REST `PUT/PATCH/DELETE`.

## Frontend routes (workflow inventory for frontend-surface tasks)

Dashboard (KPI cards: today's appointments, boarding occupancy %, vaccinations
due this week, outstanding balance) · schedule/calendar (day grid,
`appointment_date` equality filter) · schedule/waitlist · patients list/detail
(overview/records/vaccinations/medications/imaging/documents/boarding-history) ·
owners list/detail (merge-duplicates tool) · boarding/runs (live occupancy board
→ check-in/check-out actions) · boarding/reservations (vaccination gate at
check-in: rabies lapse check via latest rabies due_date) · boarding/daily-log
(checklist per reservation per day) · locations list/settings/transfers
(approve → rewrites `patients.location_id` + audit entry) · providers
list/schedule · inventory pharmacy/supplies/controlled-substances (CS tab
read-only, append-only log) · billing/invoices · billing/estimates · reports
(visits-by-species, vaccination-compliance, boarding-occupancy,
revenue-by-location via `/v1/sql/query` join) · settings
users-roles/locations/fee-schedules/reminder-templates.

Key frontend behaviors replicated by frontend-surface gold solutions (grounded
in `src/pages/**`):
- **Check-in** (`boarding/runs.tsx`): reservation → `checked_in`, run →
  `occupied` + `current_patient_id`.
- **Check-out**: run → `cleaning`, reservation → `checked_out`; later run → `available`.
- **Transfer approval** (`locations/transfers.tsx`): transfer → approved/completed,
  `patients.location_id` rewrite, `audit_log` append.
- **Send Reminder** (`patients/vaccinations.tsx`): batch-enqueue overdue vaccine
  reminders into `reminder_queue`.
- **Records lock**: notes older than 30 days get `locked_at`; amendments append a
  new linked record (immutable-note rule).
- **Estimate conversion**: accepted estimate → new invoice (`ESTIMATE_CONVERTED` audit).

## Manifest vs live

The current image's `/rl/manifest.json` reports the correct single-underscore
`collection_prefix` (`veterinary_clinic_system_`) and matching table names. The
env still derives the prefix from `app_slug` defensively (an older build
reported `veterinary_clinic_system__`). Manifest has no `ops_meta` collection —
the env creates `veterinary_clinic_system_ops_meta` at `reset()` for the
per-episode nonce (runtime injection; not part of the image).
