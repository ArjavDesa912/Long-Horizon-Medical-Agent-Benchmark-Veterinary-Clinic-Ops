#!/usr/bin/env python3
"""Gold solution for 028_draft_invoice_purge (hardmode v2).

Run against a FRESH container. Idempotent: safe to run twice in the same episode.
"""
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def _build_report_and_comms(g, affected, batch, ep, ep_ts, locations):
    """Given the list of deleted draft documents, push comms and the ops report."""
    invoices_deleted = sum(1 for d in affected if d["type"] == "invoice")
    estimates_deleted = sum(1 for d in affected if d["type"] == "estimate")

    owners = sorted(set(str(d["owner_id"]) for d in affected if d.get("owner_id") is not None))
    patients = sorted(set(str(d["patient_id"]) for d in affected if d.get("patient_id") is not None))

    location_breakdown = defaultdict(int)
    for d in affected:
        loc = locations.get(str(d.get("location_id")))
        if loc:
            location_breakdown[loc["name"]] += 1

    affected_docs = sorted(affected, key=lambda x: x["document_number"])

    # Idempotent overwrite of this batch's report.
    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for r in existing_reports:
        if r.get("report") == "draft_purge" and r.get("batch_code") == batch:
            g.delete("ops_reports", r["id"])

    g.push("ops_reports", {
        "report": "draft_purge",
        "batch_code": batch,
        "episode_date": ep,
        "invoices_deleted": invoices_deleted,
        "estimates_deleted": estimates_deleted,
        "total_deleted": len(affected),
        "affected_owners": owners,
        "affected_patients": patients,
        "affected_documents": affected_docs,
        "location_breakdown": dict(location_breakdown),
    })

    # Idempotent overwrite of this batch's communications.
    try:
        existing_comms = g.all("communications")
    except RuntimeError:
        existing_comms = []
    stale_subj = f"Draft document cancelled {batch}"
    for r in existing_comms:
        if r.get("subject") == stale_subj:
            g.delete("communications", r["id"])

    for d in affected:
        g.push("communications", {
            "channel": "email",
            "direction": "outbound",
            "subject": stale_subj,
            "body": f"Draft {d['document_number']} has been removed from our system.",
            "logged_by": "Billing",
            "occurred_at": ep_ts,
            "owner_id": d["owner_id"],
            "patient_id": d["patient_id"],
        })


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"

    locations = {str(r["id"]): r for r in g.all("locations")}

    # ---- Idempotency: if the purge report already exists, replay from it ----
    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for r in existing_reports:
        if r.get("report") == "draft_purge" and r.get("batch_code") == batch:
            affected = r.get("affected_documents") or []
            _build_report_and_comms(g, affected, batch, ep, ep_ts, locations)
            print(f"gold done (idempotent replay) in {g.steps} API calls")
            return

    # ---- First run: collect and delete all draft documents ----
    affected = []

    for r in g.all("billing_invoices"):
        if r.get("status") == "draft":
            affected.append({
                "type": "invoice",
                "document_number": r.get("invoice_number"),
                "owner_id": r.get("owner_id"),
                "patient_id": r.get("patient_id"),
                "location_id": r.get("location_id"),
            })
            g.delete("billing_invoices", r["id"])

    for r in g.all("billing_estimates"):
        if r.get("status") == "draft":
            affected.append({
                "type": "estimate",
                "document_number": r.get("estimate_number"),
                "owner_id": r.get("owner_id"),
                "patient_id": r.get("patient_id"),
                "location_id": r.get("location_id"),
            })
            g.delete("billing_estimates", r["id"])

    _build_report_and_comms(g, affected, batch, ep, ep_ts, locations)

    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
