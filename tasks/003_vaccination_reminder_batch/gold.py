#!/usr/bin/env python3
"""Gold solution for 003_vaccination_reminder_batch (run against a FRESH container)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    patients = {str(r["id"]): r for r in g.all("patients")}
    vaccs = g.all("vaccinations")
    queue = g.all("reminder_queue")
    existing = set(str(r.get("patient_id")) for r in queue if r.get("kind") == "vaccination_due" and r.get("status") == "queued")
    overdue = {}
    for r in vaccs:
        due = glib.Gold.dp(r.get("due_date"))
        if due and due < ep:
            pid = str(r.get("patient_id"))
            if pid not in overdue or due < overdue[pid][0]:
                overdue[pid] = (due, r)
    for pid, (due, vr) in overdue.items():
        if pid in existing:
            continue
        p = patients.get(pid, {})
        g.push("reminder_queue", {
            "kind": "vaccination_due",
            "patient_id": pid,
            "due_date": due,
            "status": "queued",
            "queued_by": "admin@pawsclinic.com",
            "queued_at": ep_ts,
            "message": f"{p.get('name')} is overdue for {vr.get('vaccine_type')} — call to book a nurse visit.",
        })


if __name__ == "__main__":
    main()
