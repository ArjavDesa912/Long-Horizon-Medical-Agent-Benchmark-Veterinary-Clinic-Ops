#!/usr/bin/env python3
"""Verifier for 022_ar_aging_report (hardmode v2).

AR aging + reconciliation. No source mutations allowed. Verify ops_reports
rows and one audit row; all other collections byte-identical. Dual-path
aggregates (Python vs SQL) must agree.
"""
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def _bucket(age: int) -> str:
    if 0 <= age <= 30:
        return "bucket_0_30"
    elif 31 <= age <= 60:
        return "bucket_31_60"
    elif 61 <= age <= 90:
        return "bucket_61_90"
    else:
        return "bucket_90_plus"


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()

    seed_inv = vlib.seed_rows("billing_invoices")
    live_inv = vlib.fetch_all(v.token, "billing_invoices")
    seed_own = vlib.seed_rows("owners")
    live_own = vlib.fetch_all(v.token, "owners")
    locations = {str(r["id"]): r for r in vlib.fetch_all(v.token, "locations")}

    # No source mutation canary on invoice and owner ledgers.
    v.expect_equal(len(live_inv), len(seed_inv), "billing_invoices count (must be unchanged)")
    v.expect_equal(len(live_own), len(seed_own), "owners count (must be unchanged)")
    for a, b, label in [(seed_inv, live_inv, "billing_invoices"), (seed_own, live_own, "owners")]:
        for r in a:
            rid = str(r["id"])
            live = next((x for x in b if str(x.get("id")) == rid), None)
            v.expect(live is not None, f"{label} {rid} missing")
            v.expect(vlib.row_eq(live, r, ignore=("updated_at",)), f"{label} {rid} changed unexpectedly")

    # Python path: open AR, buckets, per-owner, per-location.
    open_invs = [
        r for r in live_inv
        if r.get("status") in ("sent", "overdue")
        and (vlib.cents(r.get("total_amount")) - vlib.cents(r.get("amount_paid"))) > 0
    ]
    py_total = sum(
        vlib.cents(r.get("total_amount")) - vlib.cents(r.get("amount_paid")) for r in open_invs
    )

    py_buckets = {
        "bucket_0_30": 0,
        "bucket_31_60": 0,
        "bucket_61_90": 0,
        "bucket_90_plus": 0,
    }
    py_loc = {
        str(k): {
            "bucket_0_30": 0,
            "bucket_31_60": 0,
            "bucket_61_90": 0,
            "bucket_90_plus": 0,
            "invoice_count": 0,
            "open_total": 0,
        }
        for k in locations
    }
    py_owner = defaultdict(int)
    for r in open_invs:
        issued = vlib.dp(r.get("issued_date"))
        age = (ep_dt - datetime.strptime(issued, "%Y-%m-%d").date()).days
        b = _bucket(age)
        unpaid = vlib.cents(r.get("total_amount")) - vlib.cents(r.get("amount_paid"))
        py_buckets[b] += unpaid
        loc = str(r.get("location_id"))
        py_loc[loc][b] += unpaid
        py_loc[loc]["invoice_count"] += 1
        py_loc[loc]["open_total"] += unpaid
        py_owner[str(r.get("owner_id"))] += unpaid

    # SQL path: bucket totals.
    sql_bucket = vlib.sql(
        v.token,
        f"SELECT "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 0 AND 30 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_0_30, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 31 AND 60 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_31_60, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) BETWEEN 61 AND 90 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_61_90, "
        f"SUM(CASE WHEN ('{ep}'::date - issued_date::date) > 90 THEN (total_amount - amount_paid) ELSE 0 END) as bucket_90_plus, "
        f"COUNT(*) as invoice_count "
        f"FROM veterinary_clinic_system_billing_invoices "
        f"WHERE status IN ('sent', 'overdue') AND (total_amount - amount_paid) > 0",
    )[0]
    for k in py_buckets:
        v.expect_equal(
            vlib.cents(sql_bucket.get(k)),
            py_buckets[k],
            f"{k}: SQL vs Python (dual-path)",
        )
    v.expect_equal(int(sql_bucket.get("invoice_count")), len(open_invs), "invoice_count: SQL vs Python")

    # SQL path: per-owner open AR.
    sql_owner_rows = vlib.sql(
        v.token,
        f"SELECT owner_id, SUM(total_amount - amount_paid) as unpaid "
        f"FROM veterinary_clinic_system_billing_invoices "
        f"WHERE status IN ('sent', 'overdue') AND (total_amount - amount_paid) > 0 "
        f"GROUP BY owner_id",
    )
    sql_owner = {str(r["owner_id"]): vlib.cents(r["unpaid"]) for r in sql_owner_rows}
    v.expect_equal(sql_owner, dict(py_owner), "per-owner open AR: SQL vs Python")

    # SQL path: per-location open totals.
    sql_loc_rows = vlib.sql(
        v.token,
        f"SELECT location_id, COUNT(*) as cnt, SUM(total_amount - amount_paid) as unpaid "
        f"FROM veterinary_clinic_system_billing_invoices "
        f"WHERE status IN ('sent', 'overdue') AND (total_amount - amount_paid) > 0 "
        f"GROUP BY location_id",
    )
    sql_loc = {str(r["location_id"]): {"cnt": int(r["cnt"]), "unpaid": vlib.cents(r["unpaid"])} for r in sql_loc_rows}
    # GROUP BY omits locations with zero open invoices; py_loc is initialized
    # for every location (needed below for the ops_reports row-count check),
    # so filter those zero-count entries out for this comparison only.
    py_loc_cmp = {
        k: {"cnt": v["invoice_count"], "unpaid": v["open_total"]}
        for k, v in py_loc.items() if v["invoice_count"] > 0
    }
    v.expect_equal(sql_loc, py_loc_cmp, "per-location open AR: SQL vs Python")

    # Reconciliation.
    total_owner_balance = 0
    discrepancies = 0
    for o in live_own:
        oid = str(o["id"])
        bal = vlib.cents(o.get("balance"))
        total_owner_balance += bal
        open_ar = py_owner.get(oid, 0)
        if bal != open_ar:
            discrepancies += 1

    # ops_reports rows.
    reports = vlib.fetch_all(v.token, "ops_reports")
    ar_rows = [r for r in reports if r.get("report") == "ar_aging" and r.get("batch_code") == batch]
    v.expect_equal(len(ar_rows), 1, "ar_aging row count")
    ar = ar_rows[0]
    for k in py_buckets:
        v.expect_equal(vlib.cents(ar.get(k)), py_buckets[k], f"ar_aging {k}")
    v.expect_equal(ar.get("invoice_count"), len(open_invs), "ar_aging invoice_count")

    loc_rows = [r for r in reports if r.get("report") == "ar_aging_by_location" and r.get("batch_code") == batch]
    v.expect_equal(len(loc_rows), len(locations), "ar_aging_by_location row count")
    for r in loc_rows:
        loc = str(r.get("location_id"))
        v.expect(loc in py_loc, f"unexpected location {loc}")
        exp = py_loc[loc]
        v.expect_equal(str(r.get("location_id")), loc, "location_id")
        v.expect_equal(r.get("location_name"), locations[loc].get("name"), "location_name")
        for k in ("bucket_0_30", "bucket_31_60", "bucket_61_90", "bucket_90_plus"):
            v.expect_equal(vlib.cents(r.get(k)), exp[k], f"location {loc} {k}")
        v.expect_equal(r.get("invoice_count"), exp["invoice_count"], f"location {loc} invoice_count")
        v.expect_equal(vlib.cents(r.get("open_total")), exp["open_total"], f"location {loc} open_total")

    rec_rows = [r for r in reports if r.get("report") == "ar_reconciliation_summary" and r.get("batch_code") == batch]
    v.expect_equal(len(rec_rows), 1, "ar_reconciliation_summary row count")
    rec = rec_rows[0]
    v.expect_equal(rec.get("total_owners_checked"), len(live_own), "total_owners_checked")
    v.expect_equal(rec.get("discrepancies_found"), discrepancies, "discrepancies_found")
    v.expect_equal(vlib.cents(rec.get("total_open_ar")), py_total, "total_open_ar")
    v.expect_equal(vlib.cents(rec.get("total_owner_balance")), total_owner_balance, "total_owner_balance")

    # Audit log.
    live_a = vlib.fetch_all(v.token, "audit_log")
    matches = [
        a for a in live_a
        if a.get("action") == "AR_AGING_CLOSE"
        and a.get("target_collection") == "ops_reports"
        and a.get("target_id") == batch
    ]
    v.expect_equal(len(matches), 1, "AR_AGING_CLOSE audit count")
    a = matches[0]
    expected_details = (
        f"AR aging and reconciliation closed for {batch}: "
        f"{len(open_invs)} open invoices, ${py_total / 100:.2f} open AR, "
        f"{discrepancies} owner balance discrepancies"
    )
    v.expect_equal(a.get("details"), expected_details, "audit details")
    v.expect_equal(a.get("actor"), "system", "audit actor")
    v.expect_equal(a.get("actor_role"), "system", "audit actor_role")
    v.expect_equal(vlib.dp(a.get("occurred_at")), ep, "audit occurred_at")

    # Canary for untouched collections.
    v.check_canaries([
        "appointments", "billing_estimates", "billing_invoices", "boarding_daily_log",
        "boarding_reservations", "boarding_runs", "communications", "controlled_substance_log",
        "fee_schedules", "files", "lab_results", "location_transfers", "locations",
        "medications", "owners", "patients", "pharmacy_inventory", "providers",
        "reminder_queue", "reminder_templates", "vaccinations", "visit_records", "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
