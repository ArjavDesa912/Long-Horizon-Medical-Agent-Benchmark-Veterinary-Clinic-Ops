#!/usr/bin/env python3
"""Verifier for 043_double_booking_repair.

Recompute conflict groups from LIVE post-state invariants: assert NO same date+location+room+start_time duplicates among scheduled/confirmed (unless 'needs_reschedule'); assert every moved row is snapshot-row + 30min*k shift matching the deterministic cascade and tagged with nonce; assert kept rows byte-identical; count 46. Implement by replaying the documented algorithm from snapshot and comparing the resulting full expected state for the appointments collection (ids fixed).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    batch = vlib.get_nonce(v.token)
    v.expect(batch, "nonce missing")
    seed = vlib.seed_rows("appointments")
    live = vlib.fetch_all(v.token, "appointments")
    v.expect_equal(len(live), len(seed), "appointment count")

    def _shift(t, minutes=30):
        h, m = map(int, t.split(":"))
        total = h * 60 + m + minutes
        return f"{total // 60:02d}:{total % 60:02d}"

    def _rebuild(apps, batch):
        ordered = sorted(apps, key=lambda r: (r.get("created_at"), int(r["id"])))
        occupied = {}
        placed = {}
        for r in ordered:
            rid = str(r["id"])
            if r.get("status") not in ("scheduled", "confirmed"):
                placed[rid] = r
                continue
            dt = vlib.dp(r.get("appointment_date"))
            start = r.get("start_time")
            end = r.get("end_time")
            new = dict(r)
            placed_key = None
            for k in range(0, 20):
                st = _shift(start, k * 30)
                en = _shift(end, k * 30)
                if st >= "17:00" or en > "17:00":
                    break
                key = (dt, r.get("room"), r.get("location_id"), st)
                if key not in occupied:
                    new["start_time"] = st
                    new["end_time"] = en
                    if k > 0:
                        new["rescheduled"] = batch
                    placed_key = key
                    break
            if placed_key is None:
                new["status"] = "needs_reschedule"
                new["rescheduled"] = batch
            else:
                occupied[placed_key] = rid
            placed[rid] = new
        return placed

    expected = _rebuild(seed, batch)
    seed_by_id = {str(r["id"]): r for r in seed}
    live_by_id = {str(r["id"]): r for r in live}
    for rid, s in seed_by_id.items():
        exp = expected[rid]
        actual = live_by_id[rid]
        v.expect(vlib.row_eq(actual, exp, ignore=("updated_at",)), f"appointment {rid} mismatch")
    # live invariant
    occupied = {}
    for r in live:
        if r.get("status") in ("scheduled", "confirmed"):
            key = (vlib.dp(r.get("appointment_date")), r.get("room"), r.get("location_id"), r.get("start_time"))
            v.expect(key not in occupied, f"conflict on {key}")
            occupied[key] = r

    v.check_canaries(['audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_queue', 'reminder_templates', 'vaccinations', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
