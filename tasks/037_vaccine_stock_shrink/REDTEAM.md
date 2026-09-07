# 037_vaccine_stock_shrink — REDTEAM notes (Phase 4 PENDING)

## Mission
Apply a per-episode randomized shrink percentage (ops_meta.shrink_pct, integer
5-20) to every vaccine SKU in `pharmacy_inventory` with floor rounding and
`shrink_adjusted`/`pre_shrink_qty` tagging, then reconcile the resulting stock
against real vaccination demand: one `ops_reports` `vaccine_shrink` row per
vaccine_type with pre/post doses, `demand_next_30` (inclusive 30-day window
from the episode date), and a coverage status, closed by a
`VACCINE_SHRINK_AUDIT` audit_log row.

## Why this is hard / unique
- The shrink percent is a per-episode nonce — hardcoded percentages are wrong
  on reseed, and integer-vs-fraction misuse fails float checks.
- `pre_shrink_qty` stores the pre-shrink value because `floor()` is lossy;
  the verifier derives expected post-shrink quantities from the SNAPSHOT, so
  a rerun that double-shrinks or a report that derives `pre_doses` from live
  post-shrink state both fail.
- `demand_next_30` is dual-path verified (Python raw-row filter vs SQL
  COUNT BETWEEN) over 600 vaccinations with a jittering episode date.
- Case-insensitive leading-token join from item_name to vaccine_type.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- Exactly 8 of 42 inventory rows contain 'vaccine' (ids 1-8); ids 9-18 are
  non-vaccine medications, 19-34 supplies, 35-42 controlled substances —
  verified in the snapshot. Substring-not-category selection is mandatory.
- Bordetella vaccine ids 7/8 are already at/below reorder (9 <= 10) before
  the shrink — skipping "already low" rows fails exact-quantity checks.
- vaccinations.vaccine_type casing is mixed: 'rabies', 'DHPP', 'FVRCP',
  'bordetella' — a case-sensitive join drops two of four types. Verified in
  the snapshot's 600 rows (150 per type).
- demand_next_30 at episode anchor 2026-09-30 (±3d jitter): rabies 12,
  DHPP 10, FVRCP 9, bordetella 7 — small counts where an inclusive/exclusive
  boundary error flips a coverage_status.
- `audit_log` seed row id 3 is `CS_LOG_APPENDED` — a controlled-substance
  decoy that must not be edited; exactly one new row allowed.
- `ops_reports` absent from the 24-collection snapshot — created blind.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session
with Docker access must run the 6 standard attacks (metadata inference,
partial/prefix satisfaction, canary/scope violation, evaluation-function
tampering, retry/flake, style/no-op-adjacent shortcut) against a real
container before this task ships. Do not treat this task as done until
this section is replaced with real results and `hardened_after_rounds` is
recorded.
