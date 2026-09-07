#!/usr/bin/env python3
"""Gold solution for 001_overdue_vaccine_compliance_flag (hardmode v2).

Run against a FRESH container. Idempotent: safe to run twice in the same episode.
"""
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def _flag(due: str | None, ep: str, soon_end: str) -> str:
    """Classify a date-prefix due date against the episode and 7-day window."""
    if due is None:
        return "current"
    if due < ep:
        return "overdue"
    if due <= soon_end:
        return "due_soon"
    return "current"


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    soon_end = (ep_dt + timedelta(days=7)).strftime("%Y-%m-%d")

    patients = {str(r["id"]): r for r in g.all("patients")}
    locations = {str(r["id"]): r for r in g.all("locations")}
    vaccs = g.all("vaccinations")
    queue = g.all("reminder_queue")

    # ---- Part 1: set compliance_flag on every vaccination ----------------
    by_patient_flag = defaultdict(lambda: {"overdue": 0, "due_soon": 0, "current": 0})
    by_species = defaultdict(lambda: {"overdue": 0, "due_soon": 0, "current": 0})
    by_location = defaultdict(lambda: {"overdue": 0, "due_soon": 0, "current": 0})

    for r in vaccs:
        due = glib.Gold.dp(r.get("due_date"))
        flag = _flag(due, ep, soon_end)
        g.update("vaccinations", r["id"], {"compliance_flag": flag})

        pid = str(r.get("patient_id"))
        by_patient_flag[pid][flag] += 1

        patient = patients.get(pid, {})
        species = patient.get("species")
        if species:
            by_species[species][flag] += 1

        loc_id = patient.get("location_id")
        loc_name = locations.get(loc_id, {}).get("name") if loc_id else None
        if loc_name:
            by_location[loc_name][flag] += 1

    # ---- Part 2: stale reminder_queue count -----------------------------
    # Patient qualifies as "has overdue or due_soon" if any of their vaccinations
    # ended up in those buckets.
    stale = 0
    for q in queue:
        if q.get("kind") == "vaccination_due" and q.get("status") == "queued":
            pid = str(q.get("patient_id"))
            counts = by_patient_flag.get(pid, {})
            if counts.get("overdue", 0) == 0 and counts.get("due_soon", 0) == 0:
                stale += 1

    # ---- Part 3: ops_reports snapshot (idempotent overwrite) ------------
    total = len(vaccs)
    overdue = sum(1 for r in vaccs if _flag(glib.Gold.dp(r.get("due_date")), ep, soon_end) == "overdue")
    due_soon = sum(1 for r in vaccs if _flag(glib.Gold.dp(r.get("due_date")), ep, soon_end) == "due_soon")
    current = total - overdue - due_soon
    compliance_pct = round(100.0 * current / total, 1) if total else 0.0

    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for r in existing_reports:
        if r.get("report") == "vaccination_compliance_snapshot" and r.get("batch_code") == batch:
            g.delete("ops_reports", r["id"])

    g.push("ops_reports", {
        "report": "vaccination_compliance_snapshot",
        "batch_code": batch,
        "total_vaccinations": total,
        "overdue_count": overdue,
        "due_soon_count": due_soon,
        "current_count": current,
        "compliance_pct": compliance_pct,
        "stale_reminder_count": stale,
        "breakdown_by_species": dict(by_species),
        "breakdown_by_location": dict(by_location),
    })


if __name__ == "__main__":
    main()
