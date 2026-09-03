#!/usr/bin/env python3
"""Gold solution for 022_ar_aging_report (run against a FRESH container)."""
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    batch = g.nonce()
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    inv = g.all("billing_invoices")
    buckets = defaultdict(int)
    count = 0
    for r in inv:
        if r.get("status") not in ("sent", "overdue"):
            continue
        unpaid = glib.Gold.cents(r.get("total_amount")) - glib.Gold.cents(r.get("amount_paid"))
        if unpaid <= 0:
            continue
        age = (ep_dt - datetime.strptime(glib.Gold.dp(r.get("issued_date")), "%Y-%m-%d").date()).days
        count += 1
        if 0 <= age <= 30:
            buckets["bucket_0_30"] += unpaid
        elif 31 <= age <= 60:
            buckets["bucket_31_60"] += unpaid
        elif 61 <= age <= 90:
            buckets["bucket_61_90"] += unpaid
        else:
            buckets["bucket_90_plus"] += unpaid
    g.push("ops_reports", {
        "report": "ar_aging",
        "batch_code": batch,
        "bucket_0_30": buckets["bucket_0_30"] / 100.0,
        "bucket_31_60": buckets["bucket_31_60"] / 100.0,
        "bucket_61_90": buckets["bucket_61_90"] / 100.0,
        "bucket_90_plus": buckets["bucket_90_plus"] / 100.0,
        "invoice_count": count,
    })



if __name__ == "__main__":
    main()
