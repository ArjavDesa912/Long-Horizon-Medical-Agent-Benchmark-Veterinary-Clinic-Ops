#!/usr/bin/env python3
"""Gold solution for 002_rabies_booster_due_recompute (hardmode v2).

Recomputes canine rabies due dates as administered_date + 1 year, then runs the
full batch audit: reminders + owner communications for due/overdue patients,
an ops_reports batch summary, and an audit_log entry. Idempotent.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def one_year_after(adm: str) -> str:
    """Return adm + 1 year, Feb 29 -> Feb 28."""
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
    end_dt = ep_dt + timedelta(days=30)
    end = end_dt.strftime("%Y-%m-%d")

    patients = {str(r["id"]): r for r in g.all("patients")}
    vaccs = g.all("vaccinations")
    queue = g.all("reminder_queue")
    comms = g.all("communications")
    inventory = g.all("pharmacy_inventory")

    # Identify existing rows we created (for idempotency).
    existing_q_keys = {
        (str(r.get("patient_id")), glib.Gold.dp(r.get("due_date")))
        for r in queue
        if r.get("kind") == "vaccination_due" and r.get("status") == "queued"
    }
    existing_subj = f"Rabies booster recompute {batch}"
    existing_c_pids = {str(r.get("patient_id")) for r in comms if r.get("subject") == existing_subj}

    total = overdue = due_next_30 = current = 0
    needs_attention = []  # (patient_id, new_due)

    for r in vaccs:
        pid = str(r.get("patient_id"))
        p = patients.get(pid)
        if not p or p.get("species") != "canine":
            continue
        if r.get("vaccine_type") != "rabies":
            continue
        adm = glib.Gold.dp(r.get("administered_date"))
        new_due = one_year_after(adm)
        new_due_ts = new_due + "T00:00:00.000Z"
        g.update("vaccinations", r["id"], {"due_date": new_due_ts})

        total += 1
        if new_due < ep:
            overdue += 1
        elif new_due <= end:
            due_next_30 += 1
        else:
            current += 1

        if new_due <= end:
            needs_attention.append((pid, new_due))

    # Reminder and communication for each affected patient within the 30-day window.
    for pid, new_due in needs_attention:
        p = patients[pid]
        if (pid, new_due) in existing_q_keys:
            pass  # already queued
        else:
            g.push("reminder_queue", {
                "kind": "vaccination_due",
                "patient_id": pid,
                "due_date": new_due + "T00:00:00.000Z",
                "status": "queued",
                "queued_by": "admin@pawsclinic.com",
                "queued_at": ep_ts,
                "message": f"{p['name']} rabies booster due {new_due} — call to book a nurse visit.",
            })
        if pid in existing_c_pids:
            pass
        else:
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

    # ops_reports: delete-then-rewrite keyed by batch.
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

    # audit_log: idempotent by action + target_id.
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

    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
