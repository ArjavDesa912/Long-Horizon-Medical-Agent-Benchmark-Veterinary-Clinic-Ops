#!/usr/bin/env python3
"""Alternate gold solution for 080_enterprise_kpi_pack.

Reaches the same end-state as gold.py but derives almost all aggregates
via server-side SQL, then pushes the same ops_reports rows.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    ep_start = ep + "T00:00:00.000Z"
    ep_end = (ep_dt + timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00.000Z"
    prefix = "veterinary_clinic_system_"

    # ---- boarding reconciliation (Python cross-check) -----------------------
    runs = g.all("boarding_runs")
    reservations = g.all("boarding_reservations")
    occupied_runs = [r for r in runs if r.get("status") == "occupied"]
    checked_in_res = [r for r in reservations if r.get("status") == "checked_in"]
    reconciliation_note = ""
    if len(occupied_runs) != len(checked_in_res):
        reconciliation_note = (
            f"boarding mismatch: {len(occupied_runs)} occupied runs vs "
            f"{len(checked_in_res)} checked-in reservations"
        )
    total_runs = len(runs)
    occ_pct = round(100.0 * len(occupied_runs) / total_runs, 1) if total_runs else 0.0

    # ---- SQL aggregates -----------------------------------------------------
    q = lambda s: g.sql(s)

    appt_sql = q(
        f"SELECT COUNT(*) as c FROM {prefix}appointments "
        f"WHERE appointment_date >= '{ep_start}' AND appointment_date < '{ep_end}'"
    )[0]["c"]

    overdue_sql = q(
        f"SELECT COUNT(*) as c FROM {prefix}vaccinations WHERE due_date < '{ep_start}'"
    )[0]["c"]

    open_sql = q(
        f"SELECT COUNT(*) as c, SUM(total_amount - amount_paid) as ar "
        f"FROM {prefix}billing_invoices WHERE status IN ('sent','overdue')"
    )[0]
    open_count = int(open_sql["c"])
    open_ar = float(open_sql["ar"] or 0)

    crit_sql = q(
        f"SELECT COUNT(*) as c FROM {prefix}lab_results WHERE flag = 'critical'"
    )[0]["c"]

    owner_bal = q(
        f"SELECT SUM(balance) as s FROM {prefix}owners"
    )[0]["s"] or 0

    # per location
    locs = q(
        f"SELECT id FROM {prefix}locations ORDER BY id"
    )
    loc_rows = []
    for loc in locs:
        lid = str(loc["id"])
        loc_appt = q(
            f"SELECT COUNT(*) as c FROM {prefix}appointments "
            f"WHERE location_id = '{lid}' AND appointment_date >= '{ep_start}' "
            f"AND appointment_date < '{ep_end}'"
        )[0]["c"]
        loc_runs_total = q(
            f"SELECT COUNT(*) as c FROM {prefix}boarding_runs WHERE location_id = '{lid}'"
        )[0]["c"]
        loc_runs_occ = q(
            f"SELECT COUNT(*) as c FROM {prefix}boarding_runs "
            f"WHERE location_id = '{lid}' AND status = 'occupied'"
        )[0]["c"]
        loc_occ_pct = round(100.0 * int(loc_runs_occ) / int(loc_runs_total), 1) if int(loc_runs_total) else 0.0
        loc_active = q(
            f"SELECT COUNT(*) as c FROM {prefix}patients "
            f"WHERE location_id = '{lid}' AND status = 'active'"
        )[0]["c"]
        loc_open = q(
            f"SELECT COUNT(*) as c, SUM(total_amount - amount_paid) as ar "
            f"FROM {prefix}billing_invoices "
            f"WHERE location_id = '{lid}' AND status IN ('sent','overdue')"
        )[0]
        loc_rows.append({
            "report": "kpi_pack",
            "batch_code": batch,
            "scope": "location",
            "location_id": lid,
            "appointments_today": int(loc_appt),
            "boarding_occupancy_pct": loc_occ_pct,
            "active_patients": int(loc_active),
            "open_invoices": int(loc_open["c"] or 0),
            "outstanding_ar_balance": float(loc_open["ar"] or 0),
        })

    # AR aging via SQL case (days overdue = ep - due_date, bucketed)
    ar_sql = q(
        f"SELECT "
        f"  SUM(CASE WHEN due_date >= DATE '{ep}' - INTERVAL '30 days' THEN total_amount - amount_paid ELSE 0 END) as b0_30, "
        f"  SUM(CASE WHEN due_date < DATE '{ep}' - INTERVAL '30 days' AND due_date >= DATE '{ep}' - INTERVAL '60 days' THEN total_amount - amount_paid ELSE 0 END) as b31_60, "
        f"  SUM(CASE WHEN due_date < DATE '{ep}' - INTERVAL '60 days' AND due_date >= DATE '{ep}' - INTERVAL '90 days' THEN total_amount - amount_paid ELSE 0 END) as b61_90, "
        f"  SUM(CASE WHEN due_date < DATE '{ep}' - INTERVAL '90 days' THEN total_amount - amount_paid ELSE 0 END) as b91_plus "
        f"FROM {prefix}billing_invoices "
        f"WHERE status IN ('sent','overdue') AND due_date <= '{ep_start}'"
    )[0]

    # ---- idempotent write --------------------------------------------------
    try:
        existing = g.all("ops_reports")
    except RuntimeError:
        existing = []
    for r in existing:
        if r.get("report") == "kpi_pack" and r.get("batch_code") == batch:
            g.delete("ops_reports", r["id"])

    g.push("ops_reports", {
        "report": "kpi_pack",
        "batch_code": batch,
        "scope": "enterprise",
        "appointments_today": int(appt_sql),
        "boarding_occupancy_pct": occ_pct,
        "vaccination_overdue": int(overdue_sql),
        "open_invoices": open_count,
        "outstanding_ar_balance": open_ar,
        "critical_labs_open": int(crit_sql),
        "outstanding_balance_total": float(owner_bal),
        "boarding_reconciliation_note": reconciliation_note,
    })
    for row in loc_rows:
        g.push("ops_reports", row)
    g.push("ops_reports", {
        "report": "kpi_pack",
        "batch_code": batch,
        "scope": "ar_aging",
        "ar_0_30": round(float(ar_sql.get("b0_30") or 0), 2),
        "ar_31_60": round(float(ar_sql.get("b31_60") or 0), 2),
        "ar_61_90": round(float(ar_sql.get("b61_90") or 0), 2),
        "ar_over_90": round(float(ar_sql.get("b91_plus") or 0), 2),
        "total_open_ar": round(open_ar, 2),
        "open_invoice_count": open_count,
    })

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
