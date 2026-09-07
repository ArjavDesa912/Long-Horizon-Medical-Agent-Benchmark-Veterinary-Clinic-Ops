#!/usr/bin/env python3
"""Alternate gold solution for 091_idempotent_reminder_send.

Reaches the same end-state as gold.py but uses a SQL GROUP BY to compute the
overdue patient set and the earliest due date per patient, then uses the live
queue to build the dedupe set.
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

    queue = g.all("reminder_queue")
    existing = set()
    for r in queue:
        dk = r.get("dedupe_key")
        if dk and str(dk).startswith("vac-"):
            existing.add(str(dk))

    overdue_rows = g.sql(
        f"SELECT patient_id, MIN(due_date) as earliest "
        f"FROM veterinary_clinic_system_vaccinations "
        f"WHERE due_date < '{ep_ts}' "
        f"GROUP BY patient_id"
    )
    overdue = {str(r["patient_id"]): glib.Gold.dp(r["earliest"]) for r in overdue_rows}

    queued = 0
    for pid in sorted(overdue):
        due = overdue[pid]
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

    doc = {
        "report": "vaccination_reminder_batch",
        "batch_code": batch,
        "overdue_patients": len(overdue),
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

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
