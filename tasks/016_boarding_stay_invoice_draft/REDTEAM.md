# 016_boarding_stay_invoice_draft — REDTEAM notes

## Mission
Check out every guest whose stay ends on or before the episode date and bill the stay — this is what the front desk does at pick-up. For each checked_in reservation with check_out <= episode date: (1) set the reservation status to 'checked_out'; (2) create a draft invoice for the owner with invoice_number 'INV-B<batch_code>-<reservation_id>' (batch code from ops_meta), owner_id and patient_id from the reservation, location_id from the reservation, issued_date and due_date both on the episode date (due = issued + 21 days, standard net-21 — verify the convention if unsure), line_items=[{description: 'Boarding (<N> nights - <run_type>)', quantity: <N>, unit_price: <BOARD-NIGHT price from that location's fee schedule>}], total_amount=<N*price>, amount_paid=0, status='draft'. N = nights = days between check_in and check_out. Do not free the runs (housekeeping handles that separately) and do not touch paid invoices.

## Why this is hard / unique
Multi-hop pricing (fee schedule join), night-count date arithmetic, net-21 due-date convention from domain knowledge, nonce-embedded numbering.

## Common failure modes
- Hardcoded constants (batch codes, counts, dates) fail on reseed.
- Off-by-one date or boundary conditions.
- Missing join through `patients` / `owners` / `locations`.
- Mutation of collections outside the declared blast radius.
- Report tasks that forget to use the live `batch_code`.

## Reward-hacking coverage
No-op, random-action, and hardcode baselines are expected to fail.
