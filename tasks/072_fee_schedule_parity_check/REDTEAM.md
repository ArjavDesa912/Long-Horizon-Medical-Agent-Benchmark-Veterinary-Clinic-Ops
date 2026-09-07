# 072_fee_schedule_parity_check — REDTEAM notes (Phase 4 PENDING)

## Mission
Corporate pricing integrity audit: fee schedule parity across locations plus a paid-invoice adherence audit against the canonical fee schedule, written to `ops_reports`.

## Why this is hard / unique
- Requires nested-array comparison of `fee_schedules.items` across locations and exact-match reconciliation of invoice line items to fee schedule descriptions.
- Fuzzy matching is a trap: descriptions like "Vaccination – rabies" and "Boarding (3 nights)" are not the canonical fee schedule names.
- Several fee schedule codes have zero paid matches but must still appear in the report.
- Dual-path verification on every numeric aggregate (Python + SQL over the nested JSONB arrays).
- Only paid invoices count; sent/draft invoices and billing_estimates are decoys.

## Hazards planted (task.json.hazards) — confirmed against seed_snapshot.json
- All three `fee_schedules` rows have identical `items` (codes WELL-EXAM/SICK-EXAM/DENTAL-PROPHY/VACC-RABIES/CBC-CHEM/BOARD-NIGHT at identical prices), so `uniform` is true only if the comparison is done on the items array.
- Non-exact-match descriptions: "Vaccination – rabies" (80), "Boarding (3 nights)" (77), "Ear cytology" (77), "Nail trim" (76).
- Fee codes SICK-EXAM, VACC-RABIES, BOARD-NIGHT have zero paid exact-match lines.
- Paid exact-match line counts: Wellness examination 87, Dental prophylaxis 77, CBC + chemistry panel 58.

## Phase 4 — NOT YET RUN
This task has not been through the live hacker-fixer loop. A QC session with Docker access must run the 6 standard attacks against a real container before this task ships.
