#!/usr/bin/env python3
"""Verifier for 080_enterprise_kpi_pack.

Recompute all six KPIs from live data vs ep; exact values (pct within 0.05, money cents); nonce.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")
    appointments = vlib.fetch_all(v.token, "appointments")
    runs = vlib.fetch_all(v.token, "boarding_runs")
    vaccinations = vlib.fetch_all(v.token, "vaccinations")
    owners = vlib.fetch_all(v.token, "owners")
    invoices = vlib.fetch_all(v.token, "billing_invoices")
    labs = vlib.fetch_all(v.token, "lab_results")
    rows = [r for r in vlib.fetch_all(v.token, "ops_reports") if r.get("report") == "kpi_pack"]
    v.expect_equal(len(rows), 1, "ops_reports row count")
    appt_today = len([a for a in appointments if vlib.dp(a.get("appointment_date")) == ep])
    total_runs = len(runs)
    occupied = len([r for r in runs if r.get("status") == "occupied"])
    occ_pct = round(100.0 * occupied / total_runs, 1) if total_runs else 0.0
    vax_overdue = len([v for v in vaccinations if vlib.dp(v.get("due_date")) < ep])
    outstanding = sum(o.get("balance", 0) for o in owners)
    open_invoices = len([i for i in invoices if i.get("status") in ("sent", "overdue")])
    critical_labs = len([l for l in labs if l.get("flag") == "critical"])
    row = rows[0]
    v.expect_equal(row.get("batch_code"), batch, "batch_code")
    v.expect_equal(row.get("report"), "kpi_pack", "report")
    v.expect_equal(vlib.dp(row.get("on_episode_date")), ep, "on_episode_date")
    v.expect_equal(row.get("appointments_today"), appt_today, "appointments_today")
    v.expect(abs(row.get("boarding_occupancy_pct") - occ_pct) < 1e-6, "boarding_occupancy_pct")
    v.expect_equal(row.get("vaccinations_overdue"), vax_overdue, "vaccinations_overdue")
    v.expect(abs(row.get("outstanding_balance_total") - outstanding) < 1e-6, "outstanding_balance_total")
    v.expect_equal(row.get("open_invoices"), open_invoices, "open_invoices")
    v.expect_equal(row.get("critical_labs_open"), critical_labs, "critical_labs_open")

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_queue', 'reminder_templates', 'vaccinations', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
