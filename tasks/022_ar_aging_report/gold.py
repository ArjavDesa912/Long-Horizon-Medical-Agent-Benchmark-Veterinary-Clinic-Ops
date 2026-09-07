#!/usr/bin/env python3
"""Gold solution for 022_ar_aging_report (hardmode v2).

Build an AR aging pack and a reconciliation summary, plus an audit entry.
Read-only on source collections; writes only ops_reports and audit_log.
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

    invoices = g.all("billing_invoices")
    owners = {str(r["id"]): r for r in g.all("owners")}
    patients = {str(r["id"]): r for r in g.all("patients")}
    locations = {str(r["id"]): r for r in g.all("locations")}

    # Open AR: sent/overdue, unpaid > 0.
    open_invs = [
        r for r in invoices
        if r.get("status") in ("sent", "overdue")
        and (glib.Gold.cents(r.get("total_amount")) - glib.Gold.cents(r.get("amount_paid"))) > 0
    ]

    # Bucket totals.
    buckets = {
        "bucket_0_30": 0,
        "bucket_31_60": 0,
        "bucket_61_90": 0,
        "bucket_90_plus": 0,
    }
    loc_buckets = {
        str(k): {
            "location_id": str(k),
            "location_name": locations[str(k)].get("name"),
            "bucket_0_30": 0,
            "bucket_31_60": 0,
            "bucket_61_90": 0,
            "bucket_90_plus": 0,
            "invoice_count": 0,
            "open_total": 0.0,
        }
        for k in locations
    }

    for r in open_invs:
        issued = glib.Gold.dp(r.get("issued_date"))
        age = (ep_dt - datetime.strptime(issued, "%Y-%m-%d").date()).days
        b = _bucket(age)
        unpaid = (glib.Gold.cents(r.get("total_amount")) - glib.Gold.cents(r.get("amount_paid"))) / 100.0
        buckets[b] += unpaid
        loc = str(r.get("location_id"))
        loc_buckets[loc][b] += unpaid
        loc_buckets[loc]["invoice_count"] += 1
        loc_buckets[loc]["open_total"] += unpaid

    # Per-owner open AR and reconciliation.
    owner_open = defaultdict(float)
    for r in open_invs:
        oid = str(r.get("owner_id"))
        unpaid = (glib.Gold.cents(r.get("total_amount")) - glib.Gold.cents(r.get("amount_paid"))) / 100.0
        owner_open[oid] += unpaid

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

    # Delete/rewrite ops_reports for this batch.
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
            "bucket_0_30": round(buckets["bucket_0_30"], 2),
            "bucket_31_60": round(buckets["bucket_31_60"], 2),
            "bucket_61_90": round(buckets["bucket_61_90"], 2),
            "bucket_90_plus": round(buckets["bucket_90_plus"], 2),
            "invoice_count": len(open_invs),
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

    # Audit log (idempotent: one per batch).
    existing_audits = g.all("audit_log")
    audit_key = ("AR_AGING_CLOSE", "ops_reports", batch)
    if not any(
        a.get("action") == audit_key[0]
        and a.get("target_collection") == audit_key[1]
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
                    f"{len(open_invs)} open invoices, ${total_open_ar:.2f} open AR, "
                    f"{discrepancies} owner balance discrepancies"
                ),
                "occurred_at": ep_ts,
            },
        )

    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
