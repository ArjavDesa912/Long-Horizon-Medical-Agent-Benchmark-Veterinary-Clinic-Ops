#!/usr/bin/env python3
"""Gold solution for 091_idempotent_reminder_send (run against a FRESH container)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():

    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    vaccs = g.all("vaccinations")
    queue = g.all("reminder_queue")
    existing = set()
    for r in queue:
        dk = r.get("dedupe_key")
        if dk and dk.startswith("vac-"):
            existing.add(dk)
    overdue = {}
    for r in vaccs:
        due = glib.Gold.dp(r.get("due_date"))
        if due and due < ep:
            pid = str(r.get("patient_id"))
            if pid not in overdue or due < overdue[pid][0]:
                overdue[pid] = (due, r)
    for pid, (due, vr) in overdue.items():
        dk = f"vac-{pid}-{batch}"
        if dk in existing:
            continue
        g.push("reminder_queue", {
            "kind": "vaccination_due",
            "patient_id": pid,
            "due_date": due + "T00:00:00.000Z",
            "message": f"Overdue vaccination reminder {batch}",
            "status": "queued",
            "queued_by": "system",
            "queued_at": ep_ts,
            "dedupe_key": dk,
        })
        existing.add(dk)



if __name__ == "__main__":
    main()
