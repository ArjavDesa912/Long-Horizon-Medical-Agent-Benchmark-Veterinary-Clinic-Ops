#!/usr/bin/env python3
"""Gold solution for 080_enterprise_kpi_pack (run against a FRESH container)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():

    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    appointments = g.all("appointments")
    runs = g.all("boarding_runs")
    vaccinations = g.all("vaccinations")
    owners = g.all("owners")
    invoices = g.all("billing_invoices")
    labs = g.all("lab_results")
    appt_today = len([a for a in appointments if glib.Gold.dp(a.get("appointment_date")) == ep])
    total_runs = len(runs)
    occupied = len([r for r in runs if r.get("status") == "occupied"])
    occ_pct = round(100.0 * occupied / total_runs, 1) if total_runs else 0.0
    vax_overdue = len([v for v in vaccinations if glib.Gold.dp(v.get("due_date")) < ep])
    outstanding = sum(o.get("balance", 0) for o in owners)
    open_invoices = len([i for i in invoices if i.get("status") in ("sent", "overdue")])
    critical_labs = len([l for l in labs if l.get("flag") == "critical"])
    g.push("ops_reports", {
        "report": "kpi_pack",
        "batch_code": batch,
        "on_episode_date": ep + "T00:00:00.000Z",
        "appointments_today": appt_today,
        "boarding_occupancy_pct": occ_pct,
        "vaccinations_overdue": vax_overdue,
        "outstanding_balance_total": outstanding,
        "open_invoices": open_invoices,
        "critical_labs_open": critical_labs,
    })



if __name__ == "__main__":
    main()
