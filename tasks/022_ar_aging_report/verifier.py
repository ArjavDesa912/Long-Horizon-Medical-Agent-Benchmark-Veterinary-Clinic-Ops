#!/usr/bin/env python3
"""Verifier for 022_ar_aging_report.

Recompute from live invoices: unpaid sent/overdue; age=(ep-dp(issued_date)).days; bucket sums in cents -> dollars; assert exact cents equality per bucket and invoice_count; single row; batch_code==nonce.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    from datetime import datetime
    from collections import defaultdict
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    batch = vlib.get_nonce(v.token)
    v.expect(ep and batch, "nonce missing")
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    inv = vlib.fetch_all(v.token, "billing_invoices")
    buckets = defaultdict(int)
    count = 0
    for r in inv:
        if r.get("status") not in ("sent", "overdue"):
            continue
        unpaid = vlib.cents(r.get("total_amount")) - vlib.cents(r.get("amount_paid"))
        if unpaid <= 0:
            continue
        age = (ep_dt - datetime.strptime(vlib.dp(r.get("issued_date")), "%Y-%m-%d").date()).days
        count += 1
        if 0 <= age <= 30:
            buckets["bucket_0_30"] += unpaid
        elif 31 <= age <= 60:
            buckets["bucket_31_60"] += unpaid
        elif 61 <= age <= 90:
            buckets["bucket_61_90"] += unpaid
        else:
            buckets["bucket_90_plus"] += unpaid
    rows = [r for r in vlib.fetch_all(v.token, "ops_reports") if r.get("report") == "ar_aging"]
    v.expect_equal(len(rows), 1, "ops_reports row count")
    row = rows[0]
    v.expect_equal(row.get("batch_code"), batch, "batch_code")
    v.expect_equal(vlib.cents(row.get("bucket_0_30")), buckets["bucket_0_30"], "bucket_0_30")
    v.expect_equal(vlib.cents(row.get("bucket_31_60")), buckets["bucket_31_60"], "bucket_31_60")
    v.expect_equal(vlib.cents(row.get("bucket_61_90")), buckets["bucket_61_90"], "bucket_61_90")
    v.expect_equal(vlib.cents(row.get("bucket_90_plus")), buckets["bucket_90_plus"], "bucket_90_plus")
    v.expect_equal(row.get("invoice_count"), count, "invoice_count")

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_queue', 'reminder_templates', 'vaccinations', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
