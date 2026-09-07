#!/usr/bin/env python3
"""Gold solution for 091_idempotent_reminder_send (hardmode v2).

Idempotent batch enqueue: one queued reminder per overdue patient keyed by
vac-<patient_id>-<batch_code>, using the patient's earliest overdue due_date.
"""
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
        if dk and str(dk).startswith("vac-"):
            existing.add(str(dk))

    overdue: dict = {}
    for r in vaccs:
        due = glib.Gold.dp(r.get("due_date"))
        if due and due < ep:
            pid = str(r.get("patient_id"))
            if pid not in overdue or due < overdue[pid][0]:
                overdue[pid] = (due, r)

    queued = 0
    for pid, (due, _vr) in sorted(overdue.items()):
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
        queued += 1

    total_overdue = len(overdue)
    doc = {
        "report": "vaccination_reminder_batch",
        "batch_code": batch,
        "overdue_patients": total_overdue,
        "queued": queued,
    }
    try:
        existing_reports = [r for r in g.all("ops_reports") if r.get("report") == "vaccination_reminder_batch" and r.get("batch_code") == batch]
    except RuntimeError:
        existing_reports = []
    if existing_reports:
        g.update("ops_reports", existing_reports[0]["id"], doc)
    else:
        g.push("ops_reports", doc)

    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
