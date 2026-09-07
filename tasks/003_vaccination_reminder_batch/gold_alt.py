#!/usr/bin/env python3
"""Alternate gold solution for 003_vaccination_reminder_batch.

SQL-first: fetch the live overdue rows with an ORDER BY patient_id, due_date,
vaccine_type, then derive the earliest per patient in Python. This differs from
gold.py's unsorted list traversal and from its batch_code-based idempotency
exclusion approach used in the write phase.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"

    # SQL-first read of all overdue vaccinations, ordered for deterministic selection.
    overdue_rows = g.sql(
        f"SELECT id, patient_id, vaccine_type, due_date "
        f"FROM veterinary_clinic_system_vaccinations "
        f"WHERE due_date < '{ep_ts}' "
        f"ORDER BY patient_id, due_date, vaccine_type"
    )

    # SQL-first read of patient names/owners.
    patient_rows = g.sql("SELECT id, name, owner_id FROM veterinary_clinic_system_patients")
    patients = {str(r["id"]): r for r in patient_rows}

    queue = g.all("reminder_queue")
    comms = g.all("communications")

    seed_queued_pids = {
        str(r.get("patient_id"))
        for r in queue
        if r.get("kind") == "vaccination_due" and r.get("status") == "queued" and r.get("batch_code") != batch
    }
    already_queued_pids = {
        str(r.get("patient_id"))
        for r in queue
        if r.get("kind") == "vaccination_due" and r.get("status") == "queued" and r.get("batch_code") == batch
    }
    subj = f"Vaccination reminder {batch}"
    existing_c_pids = {str(r.get("patient_id")) for r in comms if r.get("subject") == subj}

    # Take first row per patient because of SQL ORDER BY.
    overdue = {}
    for r in overdue_rows:
        pid = str(r["patient_id"])
        if pid not in overdue:
            overdue[pid] = (glib.Gold.dp(r["due_date"]), r["vaccine_type"])

    expected = {pid: (due, vt) for pid, (due, vt) in overdue.items() if pid not in seed_queued_pids}

    for pid, (due, vt) in expected.items():
        p = patients[pid]
        if pid not in already_queued_pids:
            g.push("reminder_queue", {
                "kind": "vaccination_due",
                "patient_id": pid,
                "due_date": due + "T00:00:00.000Z",
                "status": "queued",
                "queued_by": "admin@pawsclinic.com",
                "queued_at": ep_ts,
                "vaccine_type": vt,
                "batch_code": batch,
                "message": f"{p['name']} is overdue for {vt} — call to book a nurse visit.",
            })
        if pid not in existing_c_pids:
            g.push("communications", {
                "channel": "email",
                "direction": "outbound",
                "subject": subj,
                "body": f"{p['name']} is overdue for {vt} as of {ep}.",
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
        if r.get("batch_code") == batch and r.get("report") == "vaccination_reminder_batch":
            g.delete("ops_reports", r["id"])

    counts = Counter(vt for _, (_, vt) in expected.items())
    for vt in sorted(counts):
        g.push("ops_reports", {
            "report": "vaccination_reminder_batch",
            "batch_code": batch,
            "vaccine_type": vt,
            "reminder_count": counts[vt],
        })
    g.push("ops_reports", {
        "report": "vaccination_reminder_batch",
        "batch_code": batch,
        "vaccine_type": "ALL",
        "reminder_count": len(expected),
    })

    try:
        audit = g.all("audit_log")
    except RuntimeError:
        audit = []
    if not any(r.get("action") == "VACCINATION_REMINDER_BATCH" and r.get("target_id") == batch for r in audit):
        detail_types = ", ".join(f"{vt} {cnt}" for vt, cnt in sorted(counts.items()))
        g.push("audit_log", {
            "action": "VACCINATION_REMINDER_BATCH",
            "actor": "system",
            "actor_role": "system",
            "details": f"Batch {batch}: queued {len(expected)} vaccination-due reminders ({detail_types}).",
            "occurred_at": ep_ts,
            "target_collection": "reminder_queue",
            "target_id": batch,
        })

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
