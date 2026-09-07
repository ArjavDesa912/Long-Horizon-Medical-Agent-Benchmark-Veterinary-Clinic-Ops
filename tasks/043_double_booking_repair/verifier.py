#!/usr/bin/env python3
"""Verifier for 043_double_booking_repair (hardmode v2)."""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def _shift(t: str, minutes: int = 30) -> str:
    h, m = map(int, t.split(":"))
    total = h * 60 + m + minutes
    return f"{total // 60:02d}:{total % 60:02d}"


def _rebuild(seed, ep, batch):
    candidates = [
        r for r in seed
        if vlib.dp(r.get("appointment_date")) >= ep
        and r.get("status") in ("scheduled", "confirmed")
    ]
    ordered = sorted(candidates, key=lambda r: (r.get("created_at"), int(r["id"])))
    # Pre-existing checked-in appointments hold their slot too; a candidate
    # must never be rescheduled into one of those.
    occupied = {
        (vlib.dp(r.get("appointment_date")), r.get("location_id"), r.get("room"), r.get("start_time")): str(r["id"])
        for r in seed
        if r.get("status") == "checked_in"
    }
    placed = {}
    for r in ordered:
        rid = str(r["id"])
        dt = vlib.dp(r.get("appointment_date"))
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


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")

    seed = vlib.seed_rows("appointments")
    live = vlib.fetch_all(v.token, "appointments")
    live_audit = vlib.fetch_all(v.token, "audit_log")
    live_reports = vlib.fetch_all(v.token, "ops_reports")

    expected = _rebuild(seed, ep, batch)
    v.expect_equal(len(live), len(seed), "appointment count")

    seed_by_id = {str(r["id"]): r for r in seed}
    live_by_id = {str(r["id"]): r for r in live}
    for rid, s in seed_by_id.items():
        exp = expected.get(rid)
        actual = live_by_id[rid]
        if exp:
            v.expect(vlib.row_eq(actual, exp, ignore=("updated_at",)), f"appointment {rid} mismatch")
        else:
            v.expect(vlib.row_eq(actual, s, ignore=("updated_at",)), f"appointment {rid} changed unexpectedly")

    # live invariant: no scheduled/confirmed appointment (the ones gold
    # controls) may conflict with anything, including checked_in. Scoped to
    # appointment_date >= ep: gold's candidate selection is scoped the same
    # way, so a past-dated appointment (relative to this episode's date) was
    # never a candidate and any conflict involving it is pre-existing,
    # historical state outside gold's blast radius. A checked_in-vs-checked_in
    # collision is likewise pre-existing seed state gold can't resolve (it
    # can't move a checked-in patient), so it's out of scope too.
    occupied = {}
    for r in live:
        if r.get("status") in ("scheduled", "confirmed", "checked_in") and vlib.dp(r.get("appointment_date")) >= ep:
            key = (vlib.dp(r.get("appointment_date")), r.get("location_id"), r.get("room"), r.get("start_time"))
            prior = occupied.get(key)
            if prior is not None:
                movable = {"scheduled", "confirmed"}
                if r.get("status") in movable or prior.get("status") in movable:
                    v.expect(False, f"conflict on {key}")
            occupied[key] = r

    # ----------------------------------------------------- audit
    changed_rids = {rid for rid, r in expected.items() if r.get("rescheduled")}
    audit_rows = [a for a in live_audit if a.get("action") == "SCHEDULE_REPAIR"]
    v.expect_equal(len(audit_rows), len(changed_rids), "audit count")
    audit_targets = {str(a.get("target_id")) for a in audit_rows}
    v.expect_equal(audit_targets, changed_rids, "audit target_ids match changed appointment ids")
    for a in audit_rows:
        v.expect_equal(a.get("actor"), "system", "audit actor")
        v.expect_equal(a.get("actor_role"), "system", "audit actor_role")
        v.expect_equal(a.get("target_collection"), "appointments", "audit target_collection")
        v.expect(batch in a.get("details", ""), "audit details batch")
        v.expect(a.get("details", "").startswith("Schedule repair for appointment "), f"audit details: {a.get('details')}")

    # ----------------------------------------------------- ops_reports
    report_rows = [r for r in live_reports if r.get("report") == "schedule_repair_summary" and r.get("batch_code") == batch]
    v.expect_equal(len(report_rows), 1, "ops_reports row count")
    row = report_rows[0]

    # Python-derived counts
    py_future = len(expected)
    py_rescheduled = sum(1 for r in expected.values() if r.get("rescheduled") and r.get("status") != "needs_reschedule")
    py_needs = sum(1 for r in expected.values() if r.get("status") == "needs_reschedule")

    # SQL-derived counts. future_candidates includes needs_reschedule rows
    # too (py_future = len(expected) counts every original candidate,
    # regardless of what it ended up as) because gold.py flips some
    # candidates to that status, so live scheduled/confirmed alone
    # undercounts.
    sql_counts = vlib.sql(
        v.token,
        "SELECT status, COUNT(*) as cnt FROM veterinary_clinic_system_appointments "
        f"WHERE SUBSTRING(appointment_date::text, 1, 10) >= '{ep}' "
        f"AND (status IN ('scheduled', 'confirmed') "
        f"     OR (status = 'needs_reschedule' AND rescheduled = '{batch}')) "
        "GROUP BY status"
    )
    sql_status = {r["status"]: int(r["cnt"]) for r in sql_counts}
    sql_future = sql_status.get("scheduled", 0) + sql_status.get("confirmed", 0) + sql_status.get("needs_reschedule", 0)
    # include needs_reschedule
    sql_needs = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_appointments "
        f"WHERE SUBSTRING(appointment_date::text, 1, 10) >= '{ep}' "
        f"AND status = 'needs_reschedule' AND rescheduled = '{batch}'"
    )
    sql_needs_count = int(sql_needs[0]["cnt"]) if sql_needs else 0
    sql_rescheduled = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_appointments "
        f"WHERE SUBSTRING(appointment_date::text, 1, 10) >= '{ep}' "
        f"AND rescheduled = '{batch}' AND status IN ('scheduled', 'confirmed')"
    )
    sql_rescheduled_count = int(sql_rescheduled[0]["cnt"]) if sql_rescheduled else 0

    v.expect_equal(sql_future, py_future, "future_candidates: Python vs SQL disagree")
    v.expect_equal(sql_rescheduled_count, py_rescheduled, "rescheduled count: Python vs SQL disagree")
    v.expect_equal(sql_needs_count, py_needs, "needs_reschedule count: Python vs SQL disagree")

    v.expect_equal(row.get("future_candidates"), py_future, "future_candidates")
    v.expect_equal(row.get("rescheduled"), py_rescheduled, "rescheduled")
    v.expect_equal(row.get("needs_reschedule"), py_needs, "needs_reschedule")

    # ----------------------------------------------------- canaries
    v.check_canaries([
        "billing_estimates", "billing_invoices", "boarding_daily_log", "boarding_reservations",
        "boarding_runs", "communications", "controlled_substance_log", "fee_schedules",
        "files", "lab_results", "location_transfers", "locations", "medications",
        "owners", "patients", "pharmacy_inventory", "providers", "reminder_queue",
        "reminder_templates", "vaccinations", "visit_records", "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
