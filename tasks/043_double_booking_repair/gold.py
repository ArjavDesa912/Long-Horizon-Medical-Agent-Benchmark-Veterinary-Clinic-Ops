#!/usr/bin/env python3
"""Gold solution for 043_double_booking_repair (hardmode v2).

Idempotent: the repair is recomputed from the current appointment state and
only rows not already at the expected end-state are updated. Audit and
ops_reports are batch-keyed."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def _shift(t: str, minutes: int = 30) -> str:
    h, m = map(int, t.split(":"))
    total = h * 60 + m + minutes
    return f"{total // 60:02d}:{total % 60:02d}"


def _rebuild(appts, ep, batch):
    """Compute the deterministic expected end-state from the current rows."""
    candidates = [
        r for r in appts
        if glib.Gold.dp(r.get("appointment_date")) >= ep
        and r.get("status") in ("scheduled", "confirmed")
    ]
    ordered = sorted(candidates, key=lambda r: (r.get("created_at"), int(r["id"])))
    # Pre-existing checked-in appointments hold their slot too; a candidate
    # must never be rescheduled into one of those.
    occupied = {
        (glib.Gold.dp(r.get("appointment_date")), r.get("location_id"), r.get("room"), r.get("start_time")): str(r["id"])
        for r in appts
        if r.get("status") == "checked_in"
    }
    placed = {}
    for r in ordered:
        rid = str(r["id"])
        dt = glib.Gold.dp(r.get("appointment_date"))
        start = r.get("start_time")
        end = r.get("end_time")
        new = dict(r)
        placed_key = None
        for k in range(0, 50):
            st = _shift(start, k * 30)
            en = _shift(end, k * 30)
            if st >= "17:00" or en > "17:00":
                break
            key = (dt, r.get("location_id"), r.get("room"), st)
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


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"

    appts = g.all("appointments")
    expected = _rebuild(appts, ep, batch)
    live_by_id = {str(r["id"]): r for r in appts}

    existing_audit = g.all("audit_log")
    audited_targets = {
        str(a.get("target_id"))
        for a in existing_audit
        if a.get("action") == "SCHEDULE_REPAIR" and a.get("details") and batch in a.get("details")
    }

    for rid, exp in expected.items():
        live = live_by_id[rid]
        changed = any(live.get(k) != exp.get(k) for k in ("start_time", "end_time", "status", "rescheduled"))
        if changed:
            updates = {}
            for k in ("start_time", "end_time", "status", "rescheduled"):
                if exp.get(k) is not None and live.get(k) != exp.get(k):
                    updates[k] = exp[k]
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

    # idempotent ops_reports summary
    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for r in existing_reports:
        if r.get("report") == "schedule_repair_summary" and r.get("batch_code") == batch:
            g.delete("ops_reports", r["id"])

    # Re-derive counts from live post-mutation state.
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

    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
