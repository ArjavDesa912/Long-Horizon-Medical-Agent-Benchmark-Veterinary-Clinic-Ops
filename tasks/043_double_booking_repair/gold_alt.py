#!/usr/bin/env python3
"""Alternate gold solution for 043_double_booking_repair.

Materially different: groups conflict keys first with a dictionary, then within
each group assigns slots by sorted created_at. Uses SQL to fetch candidates and
returns the same end-state as gold.py."""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def _shift(t: str, minutes: int = 30) -> str:
    h, m = map(int, t.split(":"))
    total = h * 60 + m + minutes
    return f"{total // 60:02d}:{total % 60:02d}"


def _rebuild_grouped(appts, ep, batch):
    candidates = [
        r for r in appts
        if glib.Gold.dp(r.get("appointment_date")) >= ep
        and r.get("status") in ("scheduled", "confirmed")
    ]
    # group by original conflict key
    groups = defaultdict(list)
    for r in candidates:
        key = (
            glib.Gold.dp(r.get("appointment_date")),
            r.get("location_id"),
            r.get("room"),
            r.get("start_time"),
        )
        groups[key].append(r)

    occupied = set()
    placed = {}
    for r in candidates:
        rid = str(r["id"])
        dt = glib.Gold.dp(r.get("appointment_date"))
        start = r.get("start_time")
        end = r.get("end_time")
        # within its group, sort by (created_at, id) to determine who keeps
        key = (dt, r.get("location_id"), r.get("room"), start)
        group = sorted(groups[key], key=lambda x: (x.get("created_at"), int(x["id"])))
        if str(group[0]["id"]) != rid:
            # not the keeper; must shift. Find first k that does not collide
            # with anything already placed globally or with a keeper.
            new = dict(r)
            placed_key = None
            for k in range(1, 50):
                st = _shift(start, k * 30)
                en = _shift(end, k * 30)
                if st >= "17:00" or en > "17:00":
                    break
                candidate_key = (dt, r.get("location_id"), r.get("room"), st)
                if candidate_key not in occupied:
                    new["start_time"] = st
                    new["end_time"] = en
                    new["rescheduled"] = batch
                    placed_key = candidate_key
                    break
            if placed_key is None:
                new["status"] = "needs_reschedule"
                new["rescheduled"] = batch
            else:
                occupied.add(placed_key)
            placed[rid] = new
        else:
            # keeper stays at original slot
            new = dict(r)
            new["start_time"] = start
            new["end_time"] = end
            occupied.add((dt, r.get("location_id"), r.get("room"), start))
            placed[rid] = new
    return placed


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"

    candidates = g.sql(
        "SELECT id, appointment_date, location_id, room, start_time, end_time, status, created_at "
        "FROM veterinary_clinic_system_appointments "
        f"WHERE SUBSTRING(appointment_date::text, 1, 10) >= '{ep}' "
        "AND status IN ('scheduled', 'confirmed') "
        "ORDER BY created_at, id"
    )
    # full rows are needed for live state comparison
    appts = g.all("appointments")
    expected = _rebuild_grouped(appts, ep, batch)
    live_by_id = {str(r["id"]): r for r in appts}

    existing_audit = g.all("audit_log")
    audited_targets = {
        str(a.get("target_id"))
        for a in existing_audit
        if a.get("action") == "SCHEDULE_REPAIR" and a.get("details") and batch in a.get("details")
    }

    for rid, exp in expected.items():
        live = live_by_id[rid]
        updates = {}
        for k in ("start_time", "end_time", "status", "rescheduled"):
            if exp.get(k) is not None and live.get(k) != exp.get(k):
                updates[k] = exp[k]
        if updates:
            g.update("appointments", rid, updates)
        if exp.get("rescheduled") and rid not in audited_targets:
            g.push("audit_log", {
                "actor": "system",
                "actor_role": "system",
                "action": "SCHEDULE_REPAIR",
                "target_collection": "appointments",
                "target_id": rid,
                "details": f"Schedule repair for appointment {rid} ({batch})",
                "occurred_at": ep_ts,
            })
            audited_targets.add(rid)

    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for r in existing_reports:
        if r.get("report") == "schedule_repair_summary" and r.get("batch_code") == batch:
            g.delete("ops_reports", r["id"])

    live_appts = g.all("appointments")
    future_candidates = [
        r for r in live_appts
        if glib.Gold.dp(r.get("appointment_date")) >= ep
        and (r.get("status") in ("scheduled", "confirmed") or (r.get("status") == "needs_reschedule" and r.get("rescheduled") == batch))
    ]
    rescheduled_count = sum(
        1 for r in live_appts
        if glib.Gold.dp(r.get("appointment_date")) >= ep
        and r.get("rescheduled") == batch
        and r.get("status") in ("scheduled", "confirmed")
    )
    needs_count = sum(
        1 for r in live_appts
        if glib.Gold.dp(r.get("appointment_date")) >= ep
        and r.get("rescheduled") == batch
        and r.get("status") == "needs_reschedule"
    )

    g.push("ops_reports", {
        "report": "schedule_repair_summary",
        "batch_code": batch,
        "future_candidates": len(future_candidates),
        "rescheduled": rescheduled_count,
        "needs_reschedule": needs_count,
    })

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
