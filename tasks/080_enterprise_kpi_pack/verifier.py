#!/usr/bin/env python3
"""Verifier for 080_enterprise_kpi_pack (hardmode v2).

Every aggregate is recomputed two independent ways (Python filter over
fetch_all() data and SQL GROUP BY/SUM/COUNT) and the two must agree with each
other and with the ops_reports rows the agent wrote.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402

PREFIX = "veterinary_clinic_system_"


def _as_float(x) -> float:
    return float(x) if x is not None else 0.0


def _as_int(x) -> int:
    return int(x) if x is not None else 0


def _py_aging(open_invs, ep_dt):
    buckets = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "91+": 0.0}
    for r in open_invs:
        due = vlib.dp(r.get("due_date"))
        if not due:
            continue
        due_dt = datetime.strptime(due, "%Y-%m-%d").date()
        days = (ep_dt - due_dt).days
        if days < 0:
            continue
        unpaid = r.get("total_amount", 0) - r.get("amount_paid", 0)
        if days <= 30:
            buckets["0-30"] += unpaid
        elif days <= 60:
            buckets["31-60"] += unpaid
        elif days <= 90:
            buckets["61-90"] += unpaid
        else:
            buckets["91+"] += unpaid
    return buckets


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    ep_start = ep + "T00:00:00.000Z"
    ep_end = (ep_dt + timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00.000Z"

    # ----------------------------------------------------------------- reads
    appointments = vlib.fetch_all(v.token, "appointments")
    runs = vlib.fetch_all(v.token, "boarding_runs")
    reservations = vlib.fetch_all(v.token, "boarding_reservations")
    vaccs = vlib.fetch_all(v.token, "vaccinations")
    invoices = vlib.fetch_all(v.token, "billing_invoices")
    labs = vlib.fetch_all(v.token, "lab_results")
    owners = vlib.fetch_all(v.token, "owners")
    patients = vlib.fetch_all(v.token, "patients")
    locations = vlib.fetch_all(v.token, "locations")
    rows = [r for r in vlib.fetch_all(v.token, "ops_reports") if r.get("report") == "kpi_pack" and r.get("batch_code") == batch]

    location_ids = sorted({str(r["id"]) for r in locations}, key=int)

    # ---------------------------------------------------- Python computation
    appt_today = [r for r in appointments if vlib.dp(r.get("appointment_date")) == ep]
    occupied_runs = [r for r in runs if r.get("status") == "occupied"]
    checked_in_res = [r for r in reservations if r.get("status") == "checked_in"]
    v.expect_equal(len(occupied_runs), len(checked_in_res), "boarding runs vs reservations disagree")

    total_runs = len(runs)
    occ_pct = round(100.0 * len(occupied_runs) / total_runs, 1) if total_runs else 0.0
    vax_overdue = [r for r in vaccs if vlib.dp(r.get("due_date")) and vlib.dp(r.get("due_date")) < ep]
    open_invs = [r for r in invoices if r.get("status") in ("sent", "overdue")]
    open_ar = sum(r.get("total_amount", 0) - r.get("amount_paid", 0) for r in open_invs)
    crit_labs = [r for r in labs if r.get("flag") == "critical"]
    owner_balance = sum(r.get("balance", 0) for r in owners)

    py_loc = {}
    for lid in location_ids:
        loc_appts = [r for r in appt_today if str(r.get("location_id")) == lid]
        loc_runs = [r for r in runs if str(r.get("location_id")) == lid]
        loc_occupied = [r for r in loc_runs if r.get("status") == "occupied"]
        loc_occ_pct = round(100.0 * len(loc_occupied) / len(loc_runs), 1) if loc_runs else 0.0
        loc_active = [r for r in patients if str(r.get("location_id")) == lid and r.get("status") == "active"]
        loc_open = [r for r in open_invs if str(r.get("location_id")) == lid]
        loc_ar = sum(r.get("total_amount", 0) - r.get("amount_paid", 0) for r in loc_open)
        py_loc[lid] = {
            "appointments_today": len(loc_appts),
            "boarding_occupancy_pct": loc_occ_pct,
            "active_patients": len(loc_active),
            "open_invoices": len(loc_open),
            "outstanding_ar_balance": loc_ar,
        }

    py_buckets = _py_aging(open_invs, ep_dt)

    # ------------------------------------------------------------- SQL dual
    sql_prefix = PREFIX

    sql_appt = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as c FROM {sql_prefix}appointments "
        f"WHERE appointment_date >= '{ep_start}' AND appointment_date < '{ep_end}'"
    )[0]["c"]
    v.expect_equal(_as_int(sql_appt), len(appt_today), "dual-path: appointments_today")

    sql_overdue = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as c FROM {sql_prefix}vaccinations WHERE due_date < '{ep_start}'"
    )[0]["c"]
    v.expect_equal(_as_int(sql_overdue), len(vax_overdue), "dual-path: vaccination_overdue")

    sql_open = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as c, SUM(total_amount - amount_paid) as ar "
        f"FROM {sql_prefix}billing_invoices WHERE status IN ('sent','overdue')"
    )[0]
    v.expect_equal(_as_int(sql_open["c"]), len(open_invs), "dual-path: open_invoices count")
    v.expect_equal(_as_float(sql_open["ar"]), open_ar, "dual-path: open_invoices ar")

    sql_crit = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as c FROM {sql_prefix}lab_results WHERE flag = 'critical'"
    )[0]["c"]
    v.expect_equal(_as_int(sql_crit), len(crit_labs), "dual-path: critical_labs_open")

    sql_bal = vlib.sql(
        v.token,
        f"SELECT SUM(balance) as s FROM {sql_prefix}owners"
    )[0]["s"]
    v.expect_equal(_as_float(sql_bal), owner_balance, "dual-path: outstanding_balance_total")

    for lid in location_ids:
        loc_sql = vlib.sql(
            v.token,
            f"SELECT COUNT(*) as c, SUM(total_amount - amount_paid) as ar "
            f"FROM {sql_prefix}billing_invoices "
            f"WHERE location_id = '{lid}' AND status IN ('sent','overdue')"
        )[0]
        v.expect_equal(_as_int(loc_sql["c"]), py_loc[lid]["open_invoices"], f"dual-path loc {lid} open_invoices")
        v.expect_equal(_as_float(loc_sql["ar"]), py_loc[lid]["outstanding_ar_balance"], f"dual-path loc {lid} ar")

        loc_appt_sql = vlib.sql(
            v.token,
            f"SELECT COUNT(*) as c FROM {sql_prefix}appointments "
            f"WHERE location_id = '{lid}' AND appointment_date >= '{ep_start}' "
            f"AND appointment_date < '{ep_end}'"
        )[0]["c"]
        v.expect_equal(_as_int(loc_appt_sql), py_loc[lid]["appointments_today"], f"dual-path loc {lid} appointments")

        loc_active_sql = vlib.sql(
            v.token,
            f"SELECT COUNT(*) as c FROM {sql_prefix}patients "
            f"WHERE location_id = '{lid}' AND status = 'active'"
        )[0]["c"]
        v.expect_equal(_as_int(loc_active_sql), py_loc[lid]["active_patients"], f"dual-path loc {lid} active_patients")

        loc_occ_sql = vlib.sql(
            v.token,
            f"SELECT "
            f"  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'occupied') / COUNT(*), 1) as pct "
            f"FROM {sql_prefix}boarding_runs WHERE location_id = '{lid}'"
        )[0]["pct"]
        v.expect(
            abs(_as_float(loc_occ_sql) - py_loc[lid]["boarding_occupancy_pct"]) <= 0.05,
            f"dual-path loc {lid} occupancy_pct",
        )

    sql_ar_aging = vlib.sql(
        v.token,
        f"SELECT "
        f"  SUM(CASE WHEN due_date >= DATE '{ep}' - INTERVAL '30 days' THEN total_amount - amount_paid ELSE 0 END) as b0_30, "
        f"  SUM(CASE WHEN due_date < DATE '{ep}' - INTERVAL '30 days' AND due_date >= DATE '{ep}' - INTERVAL '60 days' THEN total_amount - amount_paid ELSE 0 END) as b31_60, "
        f"  SUM(CASE WHEN due_date < DATE '{ep}' - INTERVAL '60 days' AND due_date >= DATE '{ep}' - INTERVAL '90 days' THEN total_amount - amount_paid ELSE 0 END) as b61_90, "
        f"  SUM(CASE WHEN due_date < DATE '{ep}' - INTERVAL '90 days' THEN total_amount - amount_paid ELSE 0 END) as b91_plus "
        f"FROM {sql_prefix}billing_invoices "
        f"WHERE status IN ('sent','overdue') AND due_date <= '{ep_start}'"
    )[0]
    v.expect_equal(_as_float(sql_ar_aging["b0_30"]), py_buckets["0-30"], "dual-path ar_0_30")
    v.expect_equal(_as_float(sql_ar_aging["b31_60"]), py_buckets["31-60"], "dual-path ar_31_60")
    v.expect_equal(_as_float(sql_ar_aging["b61_90"]), py_buckets["61-90"], "dual-path ar_61_90")
    v.expect_equal(_as_float(sql_ar_aging["b91_plus"]), py_buckets["91+"], "dual-path ar_over_90")

    # ---------------------------------------------------------- ops_reports
    v.expect_equal(len(rows), 5, "ops_reports row count")
    by_scope = {r.get("scope"): r for r in rows}
    by_loc = {str(r.get("location_id")): r for r in rows if r.get("scope") == "location"}

    ent = by_scope.get("enterprise")
    v.expect(ent is not None, "missing enterprise row")
    v.expect_equal(ent.get("batch_code"), batch, "enterprise batch_code")
    v.expect_equal(ent.get("appointments_today"), len(appt_today), "appointments_today")
    v.expect(abs(ent.get("boarding_occupancy_pct") - occ_pct) < 1e-6, "boarding_occupancy_pct")
    v.expect_equal(ent.get("vaccination_overdue"), len(vax_overdue), "vaccination_overdue")
    v.expect_equal(ent.get("open_invoices"), len(open_invs), "open_invoices")
    v.expect_equal(vlib.cents(ent.get("outstanding_ar_balance")), vlib.cents(open_ar), "outstanding_ar_balance")
    v.expect_equal(ent.get("critical_labs_open"), len(crit_labs), "critical_labs_open")
    v.expect_equal(vlib.cents(ent.get("outstanding_balance_total")), vlib.cents(owner_balance), "outstanding_balance_total")

    for lid in location_ids:
        row = by_loc.get(lid)
        v.expect(row is not None, f"missing location row {lid}")
        exp = py_loc[lid]
        v.expect_equal(row.get("location_id"), lid, f"loc {lid} id")
        v.expect_equal(row.get("appointments_today"), exp["appointments_today"], f"loc {lid} appointments")
        v.expect(abs(row.get("boarding_occupancy_pct") - exp["boarding_occupancy_pct"]) < 1e-6, f"loc {lid} occupancy")
        v.expect_equal(row.get("active_patients"), exp["active_patients"], f"loc {lid} active_patients")
        v.expect_equal(row.get("open_invoices"), exp["open_invoices"], f"loc {lid} open_invoices")
        v.expect_equal(vlib.cents(row.get("outstanding_ar_balance")), vlib.cents(exp["outstanding_ar_balance"]), f"loc {lid} ar")

    ar = by_scope.get("ar_aging")
    v.expect(ar is not None, "missing ar_aging row")
    v.expect_equal(vlib.cents(ar.get("ar_0_30")), vlib.cents(round(py_buckets["0-30"], 2)), "ar_0_30")
    v.expect_equal(vlib.cents(ar.get("ar_31_60")), vlib.cents(round(py_buckets["31-60"], 2)), "ar_31_60")
    v.expect_equal(vlib.cents(ar.get("ar_61_90")), vlib.cents(round(py_buckets["61-90"], 2)), "ar_61_90")
    v.expect_equal(vlib.cents(ar.get("ar_over_90")), vlib.cents(round(py_buckets["91+"], 2)), "ar_over_90")
    v.expect_equal(vlib.cents(ar.get("total_open_ar")), vlib.cents(open_ar), "total_open_ar")
    v.expect_equal(ar.get("open_invoice_count"), len(open_invs), "open_invoice_count")

    v.check_canaries([
        "appointments", "audit_log", "billing_estimates", "billing_invoices",
        "boarding_daily_log", "boarding_reservations", "boarding_runs",
        "communications", "controlled_substance_log", "fee_schedules", "files",
        "lab_results", "location_transfers", "locations", "medications", "owners",
        "patients", "pharmacy_inventory", "providers", "reminder_queue",
        "reminder_templates", "vaccinations", "visit_records", "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
