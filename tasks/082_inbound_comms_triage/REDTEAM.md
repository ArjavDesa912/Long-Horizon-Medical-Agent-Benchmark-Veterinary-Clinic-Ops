# 082_inbound_comms_triage — REDTEAM notes (Phase 4 PENDING)

## Mission
Triage the comms inbox by adding `triage` and `route_to` to every `communications` row, then write a per-route summary to `ops_reports`. Inbound rows are routed by subject keyword; outbound rows are tagged `fyi`/`logged`.

## Why this is hard / unique
- Requires updating 160 rows while preserving all other fields.
- Subject keyword classification has order-dependent and directional rules.
- Outbound rows share the same subjects as inbound rows and must not be routed.
- The summary is verified by an independent SQL `CASE`/`GROUP BY`.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- 81 outbound and 79 inbound `communications` rows.
- Subjects and counts: 'Billing question resolved' 42 (21 in/21 out), 'Boarding dates confirmed' 35 (17 in/18 out), 'Discussed dental quote' 29 (18 in/11 out), 'Reminder call — vaccines due' 29 (13 in/16 out), 'Lab results callback' 25 (10 in/15 out).
- 'Discussed dental quote' must route to billing via 'quote'.
- 'Reminder call — vaccines due' uses 'vaccines' not 'vaccination'.
- Summary counts are inbound-only.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks before this task ships.
