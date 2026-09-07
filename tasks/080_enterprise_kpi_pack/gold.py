#!/usr/bin/env python3
"""Gold solution for 080_enterprise_kpi_pack (hardmode v2).

Aggregates 6+ collections into a 5-row ops_reports KPI pack.
Idempotent: rewrites any existing kpi_pack rows for the current batch_code.
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

    # ---- reads -------------------------------------------------------------
    appointments = g.all("appointments")
    runs = g.all("boarding_runs")
    reservations = g.all("boarding_reservations")
    vaccs = g.all("vaccinations")
    invoices = g.all("billing_invoices")
    labs = g.all("lab_results")
    owners = g.all("owners")
    patients = g.all("patients")
    locations = g.all("locations")
    location_ids = sorted({str(r["id"]) for r in locations}, key=int)

    # ---- boarding reconciliation ------------------------------------------
    occupied_runs = [r for r in runs if r.get("status") == "occupied"]
    checked_in_res = [r for r in reservations if r.get("status") == "checked_in"]
    reconciliation_note = ""
    if len(occupied_runs) != len(checked_in_res):
        reconciliation_note = (
            f"boarding mismatch: {len(occupied_runs)} occupied runs vs "
            f"{len(checked_in_res)} checked-in reservations"
        )

    # ---- enterprise aggregates --------------------------------------------
    appt_today = [r for r in appointments if glib.Gold.dp(r.get("appointment_date")) == ep]
    total_runs = len(runs)
    occ_pct = round(100.0 * len(occupied_runs) / total_runs, 1) if total_runs else 0.0
    vax_overdue = [r for r in vaccs if glib.Gold.dp(r.get("due_date")) and glib.Gold.dp(r.get("due_date")) < ep]
    open_invs = [
        r for r in invoices
        if r.get("status") in ("sent", "overdue")
    ]
    open_ar = sum(r.get("total_amount", 0) - r.get("amount_paid", 0) for r in open_invs)
    crit_labs = [r for r in labs if r.get("flag") == "critical"]
    owner_balance = sum(r.get("balance", 0) for r in owners)

    # ---- per-location aggregates ------------------------------------------
    loc_rows = []
    for lid in location_ids:
        loc_appts = [r for r in appt_today if str(r.get("location_id")) == lid]
        loc_runs = [r for r in runs if str(r.get("location_id")) == lid]
        loc_occupied = [r for r in loc_runs if r.get("status") == "occupied"]
        loc_occ_pct = round(100.0 * len(loc_occupied) / len(loc_runs), 1) if loc_runs else 0.0
        loc_active = [
            r for r in patients
            if str(r.get("location_id")) == lid and r.get("status") == "active"
        ]
        loc_open = [r for r in open_invs if str(r.get("location_id")) == lid]
        loc_ar = sum(r.get("total_amount", 0) - r.get("amount_paid", 0) for r in loc_open)
        loc_rows.append({
            "report": "kpi_pack",
            "batch_code": batch,
            "scope": "location",
            "location_id": lid,
            "appointments_today": len(loc_appts),
            "boarding_occupancy_pct": loc_occ_pct,
            "active_patients": len(loc_active),
            "open_invoices": len(loc_open),
            "outstanding_ar_balance": loc_ar,
        })

    # ---- AR aging ----------------------------------------------------------
    buckets = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "91+": 0.0}
    for r in open_invs:
        due = glib.Gold.dp(r.get("due_date"))
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
        "appointments_today": len(appt_today),
        "boarding_occupancy_pct": occ_pct,
        "vaccination_overdue": len(vax_overdue),
        "open_invoices": len(open_invs),
        "outstanding_ar_balance": open_ar,
        "critical_labs_open": len(crit_labs),
        "outstanding_balance_total": owner_balance,
        "boarding_reconciliation_note": reconciliation_note,
    })
    for row in loc_rows:
        g.push("ops_reports", row)
    g.push("ops_reports", {
        "report": "kpi_pack",
        "batch_code": batch,
        "scope": "ar_aging",
        "ar_0_30": round(buckets["0-30"], 2),
        "ar_31_60": round(buckets["31-60"], 2),
        "ar_61_90": round(buckets["61-90"], 2),
        "ar_over_90": round(buckets["91+"], 2),
        "total_open_ar": round(open_ar, 2),
        "open_invoice_count": len(open_invs),
    })

    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
