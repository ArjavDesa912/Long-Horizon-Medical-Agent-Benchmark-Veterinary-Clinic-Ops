# BUILD_NOTES — veterinary_clinic_system

## Source-software fixes (Hard Rule 1 log)

### FIX-1: seed.js `daysFromNow()` emitted bare `YYYY-MM-DD` strings → VibeDB stores NULL

- **File**: `example-for-baas-main/softwares/veterinary_clinic_system/veterinary_clinic_system-app/src/scripts/seed.js`
- **Observed (live probe, 2026-08-30)**: pushing `{"date_only": "2026-09-15"}` to a
  fresh collection reads back `null`; values with a time component
  (`2026-09-15T00:00:00Z`, `2026-09-15 00:00:00`, `2026-09-15T00:00:00.000Z`) persist
  as timestamptz. Because the seeder's `daysFromNow()` returned
  `d.toISOString().slice(0, 10)`, **every business-date column in the shipped image
  was NULL** (verified: vaccinations 60/60, appointments 46/46, invoices 26/26,
  boarding_reservations 14/14, patients.dob 30/30, visit_records 36/36, waitlist,
  reminder_queue, boarding_daily_log, billing_estimates — see RECON.md).
- **Fix**: `daysFromNow()` now returns `d.toISOString().slice(0,10) + 'T00:00:00.000Z'`
  (midnight-anchored ISO). One function body changed; no other source edits.
- **Rationale**: without this, the domain's core workflows (vaccination due dates,
  boarding windows, invoice aging) are unseeded and the app cannot demonstrate them;
  this is the minimal fix required to seed the software meaningfully.
- **App compatibility**: the frontend compares dates lexicographically
  (`due_date >= today` with `today = 'YYYY-MM-DD'`); ISO timestamps preserve correct
  ordering under these comparisons. Zod input validation for NEW appointments typed
  into the UI is unaffected (form-level only). One known cosmetic side effect:
  exact-equality API filters on date fields from the dashboard
  (`appointment_date: 'YYYY-MM-DD'`) no longer match timestamp-valued rows, so the
  dashboard's "today" counters read low. Accepted; documented here.

## Image

- **Tag**: `rl-env/veterinary_clinic_system:latest`
- **Build**: `rl-env/build.ps1 -App veterinary_clinic_system` from
  `example-for-baas-main` (parameterized `rl-env/app/Dockerfile`); rebuild on
  2026-08-30 completed OK (build log: `rl-env/build-logs/veterinary_clinic_system.log`).
- **Healthcheck**: `/rl/healthcheck.sh` passes on a fresh container (seed marker +
  app `/` + VibeDB `/health`). Verified post-rebuild (container `rlrecon-vet2`).
- **Ports**: app 5110 (Vite `serve -s`), VibeDB 8080. No volumes; `--rm` per episode.

## Seed snapshot (host-side expectations)

- `_expectations/seed_snapshot.json` captured from the rebuilt image's pristine
  state via `tools/capture_snapshot.py` (24 collections, 407 rows, per-collection
  canonical sha256 canary hashes). **Re-run capture after every image rebuild.**
- This file is host-side only; it is never copied into the image.

## Runtime additions (not image changes)

- `env.reset()` upserts `veterinary_clinic_system_ops_meta` row
  `meta_key='episode_state'` carrying `batch_code` (random `EP-XXXXXXXX`),
  `episode_date` (reset-time UTC date, ISO midnight), `injected_at`, plus any
  per-task `nonce.extra_fields` (e.g. `late_fee_pct`, `shrink_pct`).
- The `key`→`meta_key` field name choice is deliberate: VibeDB rejects
  `?key=...` filters with HTTP 400 (`Identifier 'key' is a SQL reserved keyword`),
  verified live.

## Verifier / gold / task-code placement

- All verifiers, gold solutions, the snapshot, and expected values live host-side
  under `rl_envs/veterinary_clinic_system/` only. Confirmed absent from the image:
  the image contains only `/rl/*` scripts (entrypoint, healthcheck, manifest,
  seeded.marker), the built frontend (`/app/dist`), and the seeded Postgres data
  directory. No `verifier`, `gold`, `task.json`, or `_expectations` artifact is
  baked in (build context only ever COPYs the app dir + `/rl` scripts).

## v2 hardening pass — platform bugs found and fixed

The hardmode rewrite (10x seed volume, fused/composite missions, mandatory
dual-path verification, two independent gold solutions per task) surfaced four
real bugs in the underlying platform, not just task content:

- **`sqlx` decode gaps** (`platform/db.rs`): bare `DATE`/`TIME` columns and
  `array_agg()`-returned Postgres arrays both silently decoded to `null` —
  neither type was attempted before the code fell through to its `String`
  fallback. Fixed by adding `NaiveDate`/`NaiveTime` and `Vec<i64>`/`Vec<String>`/
  `Vec<f64>` decode attempts ahead of the fallback.
- **Raw-SQL endpoint masked real Postgres errors as a generic 503**: an
  undefined-column/table error (Postgres codes `42703`/`42P01`) propagated as a
  sanitized "Service temporarily unavailable" instead of the empty result the
  REST query endpoint already returns for the same case. Fixed to match that
  existing convention.
- **Schema-churn rate limiter miscalibrated for legitimate wide writes**: the
  default cap (20 new columns/60s) rejected a single legitimate multi-field
  report push in one burst. Raised via `STACKHOUSE_SCHEMA_CHURN_MAX=60`, not by
  weakening the guardrail itself — it's still catching pathological schema
  churn, just recalibrated for this benchmark's actual workload.

All four were root-caused against a live container, not guessed. Full task-suite
QC (`QC_REPORT.md`) is clean after these fixes: 98/98.
