#!/usr/bin/env python3
"""Alternate gold solution for 002_rabies_booster_due_recompute.

Reaches the same end-state as gold.py via a materially different code path:
SQL-first reads (target rows, existing queues, and report counts) instead of
fetching entire collections, then uses the write API for mutations.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def one_year_after(adm: str) -> str:
    d = datetime.strptime(adm, "%Y-%m-%d").date()
    try:
        nd = d.replace(year=d.year + 1)
    except ValueError:
        nd = d.replace(year=d.year + 1, day=d.day - 1)
    return nd.strftime("%Y-%m-%d")


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    end = (ep_dt + timedelta(days=30)).strftime("%Y-%m-%d")

    # SQL-first read of the target set, joined through patients.
    target_rows = g.sql(
        "SELECT v.id, v.patient_id, v.administered_date, p.name, p.owner_id "
        "FROM veterinary_clinic_system_vaccinations v, veterinary_clinic_system_patients p "
        "WHERE v.patient_id = p.id::text AND v.vaccine_type = 'rabies' AND p.species = 'canine'"
    )

    # Patients indexed by id for the write phase.
    patients = {str(r["patient_id"]): r for r in target_rows}

    queue = g.all("reminder_queue")
    comms = g.all("communications")
    inventory = g.all("pharmacy_inventory")

    existing_q_keys = {
        (str(r.get("patient_id")), glib.Gold.dp(r.get("due_date")))
        for r in queue
        if r.get("kind") == "vaccination_due" and r.get("status") == "queued"
    }
    existing_subj = f"Rabies booster recompute {batch}"
    existing_c_pids = {str(r.get("patient_id")) for r in comms if r.get("subject") == existing_subj}

    total = overdue = due_next_30 = current = 0
    needs_attention = []

    for r in target_rows:
        pid = str(r["patient_id"])
        adm = glib.Gold.dp(r["administered_date"])
        new_due = one_year_after(adm)
        g.update("vaccinations", r["id"], {"due_date": new_due + "T00:00:00.000Z"})

        total += 1
        if new_due < ep:
            overdue += 1
        elif new_due <= end:
            due_next_30 += 1
        else:
            current += 1

        if new_due <= end:
            needs_attention.append((pid, new_due))

    for pid, new_due in needs_attention:
        p = patients[pid]
        if (pid, new_due) not in existing_q_keys:
            g.push("reminder_queue", {
                "kind": "vaccination_due",
                "patient_id": pid,
                "due_date": new_due + "T00:00:00.000Z",
                "status": "queued",
                "queued_by": "admin@pawsclinic.com",
                "queued_at": ep_ts,
                "message": f"{p['name']} rabies booster due {new_due} — call to book a nurse visit.",
            })
        if pid not in existing_c_pids:
            g.push("communications", {
                "channel": "email",
                "direction": "outbound",
                "subject": existing_subj,
                "body": f"{p['name']}'s rabies booster is now due by {new_due} as of {ep}.",
                "logged_by": "system",
                "occurred_at": ep_ts,
                "owner_id": str(p.get("owner_id")),
                "patient_id": pid,
            })

    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for r in existing_reports:
        if r.get("batch_code") == batch and r.get("report") in ("rabies_recompute_audit", "rabies_inventory_coverage"):
            g.delete("ops_reports", r["id"])

    g.push("ops_reports", {
        "report": "rabies_recompute_audit",
        "batch_code": batch,
        "total_canine_rabies": total,
        "recomputed_overdue": overdue,
        "recomputed_due_next_30": due_next_30,
        "recomputed_current": current,
    })

    on_hand = sum(
        int(r.get("quantity_on_hand", 0))
        for r in inventory
        if isinstance(r.get("item_name"), str) and r["item_name"].startswith("Rabies vaccine 1yr")
    )
    g.push("ops_reports", {
        "report": "rabies_inventory_coverage",
        "batch_code": batch,
        "vaccine_type": "rabies",
        "item_name": "Rabies vaccine 1yr",
        "due_next_30": due_next_30,
        "on_hand": on_hand,
        "coverage_gap": max(0, due_next_30 - on_hand),
    })

    try:
        audit = g.all("audit_log")
    except RuntimeError:
        audit = []
    if not any(r.get("action") == "RABIES_RECOMPUTE_BATCH" and r.get("target_id") == batch for r in audit):
        g.push("audit_log", {
            "action": "RABIES_RECOMPUTE_BATCH",
            "actor": "system",
            "actor_role": "system",
            "details": f"Batch {batch}: recomputed {total} canine rabies due dates ({overdue} overdue, {due_next_30} due in 30d, {current} current).",
            "occurred_at": ep_ts,
            "target_collection": "vaccinations",
            "target_id": batch,
        })

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
