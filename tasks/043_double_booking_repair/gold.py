#!/usr/bin/env python3
"""Gold solution for 043_double_booking_repair (run against a FRESH container)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():

    def _shift(t, minutes=30):
        h, m = map(int, t.split(":"))
        total = h * 60 + m + minutes
        return f"{total // 60:02d}:{total % 60:02d}"

    g = glib.Gold()
    batch = g.nonce()
    appts = g.all("appointments")
    ordered = sorted(appts, key=lambda r: (r.get("created_at"), int(r["id"])))
    occupied = {}
    for r in ordered:
        if r.get("status") not in ("scheduled", "confirmed"):
            continue
        dt = glib.Gold.dp(r.get("appointment_date"))
        start = r.get("start_time")
        end = r.get("end_time")
        new_start = start
        new_end = end
        placed_key = None
        for k in range(0, 20):
            st = _shift(start, k * 30)
            en = _shift(end, k * 30)
            if st >= "17:00" or en > "17:00":
                break
            key = (dt, r.get("room"), r.get("location_id"), st)
            if key not in occupied:
                new_start = st
                new_end = en
                placed_key = key
                break
        updates = {}
        if placed_key is None:
            updates["status"] = "needs_reschedule"
            updates["rescheduled"] = batch
        elif new_start != start:
            updates["start_time"] = new_start
            updates["end_time"] = new_end
            updates["rescheduled"] = batch
        if updates:
            g.update("appointments", r["id"], updates)
        if placed_key:
            occupied[placed_key] = r["id"]



if __name__ == "__main__":
    main()
