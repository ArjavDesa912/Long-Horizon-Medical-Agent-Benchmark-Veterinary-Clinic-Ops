#!/usr/bin/env python3
"""Alternative gold solution for 001_overdue_vaccine_compliance_flag (hardmode v2).

This version uses SQL-first reads and SQL aggregates for the report, then REST
updates/pushes. It reaches the same end-state as gold.py via a different path.
"""
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    ep_ts = ep + "T00:00:00.000Z"
    soon_end = (ep_dt + timedelta(days=7)).strftime("%Y-%m-%d")
    soon_ts = soon_end + "T00:00:00.000Z"

    # ---- SQL-first load of the small dimensions and rows to update -------
    patients = {str(r["id"]): r for r in g.sql("SELECT * FROM veterinary_clinic_system_patients")}
    locations = {str(r["id"]): r for r in g.sql("SELECT * FROM veterinary_clinic_system_locations")}
    vaccs = g.sql("SELECT id, due_date, patient_id FROM veterinary_clinic_system_vaccinations")
    queue = g.sql("SELECT * FROM veterinary_clinic_system_reminder_queue")

    # ---- Part 1: classify and update every vaccination --------------------
    def _flag(due):
        if due is None:
            return "current"
        d = glib.Gold.dp(due)
        if d < ep:
            return "overdue"
        if d <= soon_end:
            return "due_soon"
        return "current"

    by_patient_flag = defaultdict(lambda: {"overdue": 0, "due_soon": 0, "current": 0})
    for r in vaccs:
        flag = _flag(r.get("due_date"))
        g.update("vaccinations", r["id"], {"compliance_flag": flag})

        pid = str(r.get("patient_id"))
        by_patient_flag[pid][flag] += 1

    # ---- Part 2: stale reminder count (same logic, different load) ------
    stale = 0
    for q in queue:
        if q.get("kind") == "vaccination_due" and q.get("status") == "queued":
            pid = str(q.get("patient_id"))
            counts = by_patient_flag.get(pid, {})
            if counts.get("overdue", 0) == 0 and counts.get("due_soon", 0) == 0:
                stale += 1

    # ---- Part 3: SQL aggregates for the report --------------------------
    total_row = g.sql("SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations")
    total = int(total_row[0]["cnt"])

    overdue_row = g.sql(f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations WHERE due_date < '{ep_ts}'")
    overdue = int(overdue_row[0]["cnt"])

    due_soon_row = g.sql(
        f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations "
        f"WHERE due_date >= '{ep_ts}' AND due_date <= '{soon_ts}'"
    )
    due_soon = int(due_soon_row[0]["cnt"])

    current = total - overdue - due_soon
    compliance_pct = round(100.0 * current / total, 1) if total else 0.0

    by_species_rows = g.sql(
        "SELECT p.species, "
        "SUM(CASE WHEN v.due_date < '%s' THEN 1 ELSE 0 END) as overdue, "
        "SUM(CASE WHEN v.due_date >= '%s' AND v.due_date <= '%s' THEN 1 ELSE 0 END) as due_soon, "
        "SUM(CASE WHEN v.due_date > '%s' THEN 1 ELSE 0 END) as current "
        "FROM veterinary_clinic_system_vaccinations v "
        "JOIN veterinary_clinic_system_patients p ON v.patient_id::int = p.id "
        "GROUP BY p.species" % (ep_ts, ep_ts, soon_ts, soon_ts)
    )
    by_species = {}
    for row in by_species_rows:
        by_species[row["species"]] = {
            "overdue": int(row["overdue"]),
            "due_soon": int(row["due_soon"]),
            "current": int(row["current"]),
        }

    by_location_rows = g.sql(
        "SELECT l.name, "
        "SUM(CASE WHEN v.due_date < '%s' THEN 1 ELSE 0 END) as overdue, "
        "SUM(CASE WHEN v.due_date >= '%s' AND v.due_date <= '%s' THEN 1 ELSE 0 END) as due_soon, "
        "SUM(CASE WHEN v.due_date > '%s' THEN 1 ELSE 0 END) as current "
        "FROM veterinary_clinic_system_vaccinations v "
        "JOIN veterinary_clinic_system_patients p ON v.patient_id::int = p.id "
        "JOIN veterinary_clinic_system_locations l ON p.location_id::int = l.id "
        "GROUP BY l.name" % (ep_ts, ep_ts, soon_ts, soon_ts)
    )
    by_location = {}
    for row in by_location_rows:
        by_location[row["name"]] = {
            "overdue": int(row["overdue"]),
            "due_soon": int(row["due_soon"]),
            "current": int(row["current"]),
        }

    # Idempotent overwrite of the report row
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
        "breakdown_by_species": by_species,
        "breakdown_by_location": by_location,
    })


if __name__ == "__main__":
    main()
