#!/usr/bin/env python3
"""Alternate gold solution for 022_ar_aging_report.

SQL-first aggregate path: open-invoice set, bucket sums, per-owner open AR,
and per-location open AR come from the database; Python only does the
owner-balance reconciliation and the writes. If this fails while gold.py
passes, the verifier is overfit to one trajectory.
"""
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def _bucket(age: int) -> str:
    if 0 <= age <= 30:
        return "bucket_0_30"
    elif 31 <= age <= 60:
        return "bucket_31_60"
    elif 61 <= age <= 90:
        return "bucket_61_90"
    else:
        return "bucket_90_plus"


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()

    invoices = g.sql(
        f"SELECT * FROM veterinary_clinic_system_billing_invoices "
        f"WHERE status IN ('sent', 'overdue') AND (total_amount - amount_paid) > 0"
    ) or []

    bucket_sql = g.sql(
        f"SELECT "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 0 AND 30 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_0_30, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 31 AND 60 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_31_60, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 61 AND 90 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_61_90, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) > 90 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_90_plus, "
        f"COUNT(*) as invoice_count "
        f"FROM veterinary_clinic_system_billing_invoices "
        f"WHERE status IN ('sent', 'overdue') AND (total_amount - amount_paid) > 0"
    )
    bucket_row = bucket_sql[0] if bucket_sql else {}

    loc_sql = g.sql(
        f"SELECT location_id, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 0 AND 30 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_0_30, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 31 AND 60 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_31_60, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 61 AND 90 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_61_90, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) > 90 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_90_plus, "
        f"COUNT(*) as invoice_count, "
        f"SUM(total_amount - amount_paid) as open_total "
        f"FROM veterinary_clinic_system_billing_invoices "
        f"WHERE status IN ('sent', 'overdue') AND (total_amount - amount_paid) > 0 "
        f"GROUP BY location_id"
    )
    loc_sql = loc_sql or []

    owner_open_sql = g.sql(
        f"SELECT owner_id, SUM(total_amount - amount_paid) as unpaid "
        f"FROM veterinary_clinic_system_billing_invoices "
        f"WHERE status IN ('sent', 'overdue') AND (total_amount - amount_paid) > 0 "
        f"GROUP BY owner_id"
    )
    owner_open = {str(r["owner_id"]): float(r["unpaid"]) for r in (owner_open_sql or [])}

    owners = {str(r["id"]): r for r in g.all("owners")}
    locations = {str(r["id"]): r for r in g.all("locations")}

    # Derive location buckets from SQL for report writing; use Python only for reconciliation.
    loc_buckets = {
        str(k): {
            "location_id": str(k),
            "location_name": locations[str(k)].get("name"),
            "bucket_0_30": 0.0,
            "bucket_31_60": 0.0,
            "bucket_61_90": 0.0,
            "bucket_90_plus": 0.0,
            "invoice_count": 0,
            "open_total": 0.0,
        }
        for k in locations
    }
    for r in loc_sql:
        loc = str(r["location_id"])
        loc_buckets[loc]["bucket_0_30"] = float(r["bucket_0_30"] or 0)
        loc_buckets[loc]["bucket_31_60"] = float(r["bucket_31_60"] or 0)
        loc_buckets[loc]["bucket_61_90"] = float(r["bucket_61_90"] or 0)
        loc_buckets[loc]["bucket_90_plus"] = float(r["bucket_90_plus"] or 0)
        loc_buckets[loc]["invoice_count"] = int(r["invoice_count"])
        loc_buckets[loc]["open_total"] = float(r["open_total"])

    discrepancies = 0
    total_owner_balance = 0.0
    total_open_ar = sum(owner_open.values())
    for o in owners.values():
        oid = str(o["id"])
        bal = glib.Gold.cents(o.get("balance")) / 100.0
        total_owner_balance += bal
        open_ar = owner_open.get(oid, 0.0)
        if abs(bal - open_ar) > 0.005:
            discrepancies += 1

    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for rep in existing_reports:
        if rep.get("batch_code") == batch and rep.get("report") in (
            "ar_aging", "ar_aging_by_location", "ar_reconciliation_summary"
        ):
            g.delete("ops_reports", rep["id"])

    g.push(
        "ops_reports",
        {
            "report": "ar_aging",
            "batch_code": batch,
            "bucket_0_30": round(float(bucket_row.get("bucket_0_30") or 0), 2),
            "bucket_31_60": round(float(bucket_row.get("bucket_31_60") or 0), 2),
            "bucket_61_90": round(float(bucket_row.get("bucket_61_90") or 0), 2),
            "bucket_90_plus": round(float(bucket_row.get("bucket_90_plus") or 0), 2),
            "invoice_count": int(bucket_row.get("invoice_count") or 0),
        },
    )

    for loc_id in sorted(loc_buckets, key=lambda x: int(x)):
        g.push("ops_reports", {**loc_buckets[loc_id], "report": "ar_aging_by_location", "batch_code": batch})

    g.push(
        "ops_reports",
        {
            "report": "ar_reconciliation_summary",
            "batch_code": batch,
            "total_owners_checked": len(owners),
            "discrepancies_found": discrepancies,
            "total_open_ar": round(total_open_ar, 2),
            "total_owner_balance": round(total_owner_balance, 2),
        },
    )

    existing_audits = g.all("audit_log")
    if not any(
        a.get("action") == "AR_AGING_CLOSE"
        and a.get("target_collection") == "ops_reports"
        and a.get("target_id") == batch
        for a in existing_audits
    ):
        g.push(
            "audit_log",
            {
                "actor": "system",
                "actor_role": "system",
                "action": "AR_AGING_CLOSE",
                "target_collection": "ops_reports",
                "target_id": batch,
                "details": (
                    f"AR aging and reconciliation closed for {batch}: "
                    f"{len(invoices)} open invoices, ${total_open_ar:.2f} open AR, "
                    f"{discrepancies} owner balance discrepancies"
                ),
                "occurred_at": ep_ts,
            },
        )

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
