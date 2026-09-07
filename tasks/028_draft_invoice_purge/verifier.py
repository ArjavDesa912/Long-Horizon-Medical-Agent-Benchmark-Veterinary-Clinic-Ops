#!/usr/bin/env python3
"""Verifier for 028_draft_invoice_purge (hardmode v2).

Purge all draft invoices and estimates, log cancellation communications, and
write a draft_purge ops_reports row. Survivor byte-identity is enforced.
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def _parse_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise vlib.VerifierError(f"expected JSON, got non-JSON string: {value!r}")
    raise vlib.VerifierError(f"expected JSON, got {type(value).__name__}")


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    v.expect(batch and ep, "nonce missing")

    # ------------------------------------------------------------------ loads
    seed_inv = vlib.seed_rows("billing_invoices")
    live_inv = vlib.fetch_all(v.token, "billing_invoices")
    seed_est = vlib.seed_rows("billing_estimates")
    live_est = vlib.fetch_all(v.token, "billing_estimates")
    live_loc = {str(r["id"]): r for r in vlib.fetch_all(v.token, "locations")}
    live_c = vlib.fetch_all(v.token, "communications")

    seed_inv_by_id = {str(r["id"]): r for r in seed_inv}
    live_inv_by_id = {str(r["id"]): r for r in live_inv}
    seed_est_by_id = {str(r["id"]): r for r in seed_est}
    live_est_by_id = {str(r["id"]): r for r in live_est}

    # ---------------------------------------------------------------- survivors
    py_exp_inv_deleted = sum(1 for r in seed_inv if r.get("status") == "draft")
    py_exp_est_deleted = sum(1 for r in seed_est if r.get("status") == "draft")
    py_exp_total = py_exp_inv_deleted + py_exp_est_deleted

    # Invoices: no draft remains; non-draft rows byte-identical to seed.
    v.expect_equal(len(live_inv), len(seed_inv) - py_exp_inv_deleted, "live invoice count")
    for rid, seed in seed_inv_by_id.items():
        live = live_inv_by_id.get(rid)
        if seed.get("status") == "draft":
            v.expect(live is None, f"draft invoice {rid} still present")
        else:
            v.expect(live is not None, f"non-draft invoice {rid} missing")
            v.expect(
                vlib.row_eq(live, seed, ignore=("updated_at",)),
                f"non-draft invoice {rid} changed unexpectedly",
            )

    # Estimates: same.
    v.expect_equal(len(live_est), len(seed_est) - py_exp_est_deleted, "live estimate count")
    for rid, seed in seed_est_by_id.items():
        live = live_est_by_id.get(rid)
        if seed.get("status") == "draft":
            v.expect(live is None, f"draft estimate {rid} still present")
        else:
            v.expect(live is not None, f"non-draft estimate {rid} missing")
            v.expect(
                vlib.row_eq(live, seed, ignore=("updated_at",)),
                f"non-draft estimate {rid} changed unexpectedly",
            )

    # ---------------------------------------------------------------- dual-path for deleted counts
    sql_live_inv_draft = int(vlib.sql(
        v.token,
        "SELECT COUNT(*) as cnt FROM veterinary_clinic_system_billing_invoices WHERE status = 'draft'",
    )[0]["cnt"])
    sql_live_est_draft = int(vlib.sql(
        v.token,
        "SELECT COUNT(*) as cnt FROM veterinary_clinic_system_billing_estimates WHERE status = 'draft'",
    )[0]["cnt"])
    v.expect_equal(sql_live_inv_draft, 0, "live draft invoice count (SQL)")
    v.expect_equal(sql_live_est_draft, 0, "live draft estimate count (SQL)")

    sql_live_inv_non_draft = int(vlib.sql(
        v.token,
        "SELECT COUNT(*) as cnt FROM veterinary_clinic_system_billing_invoices WHERE status != 'draft'",
    )[0]["cnt"])
    sql_live_est_non_draft = int(vlib.sql(
        v.token,
        "SELECT COUNT(*) as cnt FROM veterinary_clinic_system_billing_estimates WHERE status != 'draft'",
    )[0]["cnt"])
    v.expect_equal(sql_live_inv_non_draft, len(seed_inv) - py_exp_inv_deleted, "survivor invoice count: SQL vs seed")
    v.expect_equal(sql_live_est_non_draft, len(seed_est) - py_exp_est_deleted, "survivor estimate count: SQL vs seed")

    # ---------------------------------------------------------------- expected purge list from seed
    expected_affected = []
    for r in seed_inv:
        if r.get("status") == "draft":
            expected_affected.append({
                "type": "invoice",
                "document_number": r.get("invoice_number"),
                "owner_id": r.get("owner_id"),
                "patient_id": r.get("patient_id"),
                "location_id": r.get("location_id"),
            })
    for r in seed_est:
        if r.get("status") == "draft":
            expected_affected.append({
                "type": "estimate",
                "document_number": r.get("estimate_number"),
                "owner_id": r.get("owner_id"),
                "patient_id": r.get("patient_id"),
                "location_id": r.get("location_id"),
            })
    expected_affected = sorted(expected_affected, key=lambda x: x["document_number"])
    exp_owners = sorted(set(str(d["owner_id"]) for d in expected_affected if d.get("owner_id") is not None))
    exp_patients = sorted(set(str(d["patient_id"]) for d in expected_affected if d.get("patient_id") is not None))
    exp_loc = defaultdict(int)
    for d in expected_affected:
        loc = live_loc.get(str(d.get("location_id")))
        if loc:
            exp_loc[loc["name"]] += 1

    # ---------------------------------------------------------------- ops_reports
    try:
        reports = vlib.fetch_all(v.token, "ops_reports")
    except vlib.VerifierError:
        reports = []
    purge_reports = [r for r in reports if r.get("report") == "draft_purge" and r.get("batch_code") == batch]
    v.expect_equal(len(purge_reports), 1, "draft_purge report count")
    row = purge_reports[0]

    v.expect_equal(row.get("invoices_deleted"), py_exp_inv_deleted, "report invoices_deleted")
    v.expect_equal(row.get("estimates_deleted"), py_exp_est_deleted, "report estimates_deleted")
    v.expect_equal(row.get("total_deleted"), py_exp_total, "report total_deleted")
    v.expect_equal(sorted(str(x) for x in row.get("affected_owners", [])), exp_owners, "report affected_owners")
    v.expect_equal(sorted(str(x) for x in row.get("affected_patients", [])), exp_patients, "report affected_patients")

    row_docs = _parse_json(row.get("affected_documents"))
    v.expect_equal(len(row_docs), py_exp_total, "report affected_documents count")
    for exp, got in zip(expected_affected, sorted(row_docs, key=lambda x: x.get("document_number", ""))):
        for key in ("type", "document_number", "owner_id", "patient_id", "location_id"):
            v.expect_equal(str(got.get(key)), str(exp.get(key)), f"affected_document {exp['document_number']} {key}")

    row_loc = _parse_json(row.get("location_breakdown"))
    v.expect_equal(row_loc, dict(exp_loc), "report location_breakdown")

    # ---------------------------------------------------------------- communications
    seed_c = vlib.seed_rows("communications")
    v.expect_equal(len(live_c), len(seed_c) + py_exp_total, "communications count")
    seed_c_by_id = {str(r["id"]): r for r in seed_c}
    live_c_by_id = {str(r["id"]): r for r in live_c}
    for rid, seed in seed_c_by_id.items():
        v.expect(
            vlib.row_eq(live_c_by_id[rid], seed, ignore=("updated_at",)),
            f"seeded communication {rid} changed",
        )

    stale_subj = f"Draft document cancelled {batch}"
    comms_for_batch = [r for r in live_c if r.get("subject") == stale_subj]
    v.expect_equal(len(comms_for_batch), py_exp_total, "cancellation communication count")
    for d in expected_affected:
        num = d["document_number"]
        matches = [c for c in comms_for_batch if num in (c.get("body") or "")]
        v.expect_equal(len(matches), 1, f"cancellation comm for {num}")
        c = matches[0]
        v.expect_equal(c.get("channel"), "email", f"{num} channel")
        v.expect_equal(c.get("direction"), "outbound", f"{num} direction")
        v.expect_equal(c.get("body"), f"Draft {num} has been removed from our system.", f"{num} body")
        v.expect_equal(c.get("logged_by"), "Billing", f"{num} logged_by")
        v.expect_equal(vlib.dp(c.get("occurred_at")), ep, f"{num} occurred_at")
        v.expect_equal(str(c.get("owner_id")), str(d["owner_id"]), f"{num} owner_id")
        v.expect_equal(str(c.get("patient_id")), str(d["patient_id"]), f"{num} patient_id")

    # ---------------------------------------------------------------- canaries
    v.check_canaries([
        "appointments", "audit_log", "boarding_daily_log", "boarding_reservations",
        "boarding_runs", "controlled_substance_log", "fee_schedules", "files",
        "lab_results", "location_transfers", "locations", "medications", "owners",
        "patients", "pharmacy_inventory", "providers", "reminder_queue",
        "reminder_templates", "vaccinations", "visit_records", "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
