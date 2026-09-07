#!/usr/bin/env python3
"""Alternate gold solution for 011_boarding_checkin_flow (hardmode v2).

Uses SQL to fetch the candidate set and then REST for the mutations.
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"

    # SQL candidate set
    rows = g.sql(
        f"SELECT r.id, r.patient_id, r.run_id, r.location_id, r.check_in, "
        f"runs.status as run_status, runs.current_patient_id as run_patient, "
        f"runs.run_type, runs.run_number, p.name as patient_name, "
        f"l.name as location_name "
        f"FROM veterinary_clinic_system_boarding_reservations r "
        f"JOIN veterinary_clinic_system_boarding_runs runs ON r.run_id::int = runs.id "
        f"JOIN veterinary_clinic_system_patients p ON r.patient_id::int = p.id "
        f"JOIN veterinary_clinic_system_locations l ON r.location_id::int = l.id "
        f"WHERE r.status = 'reserved' AND r.check_in <= '{ep}T00:00:00.000Z' "
        f"ORDER BY r.check_in, r.id"
    )

    patients = {str(r["id"]): r for r in g.all("patients")}
    locations = {str(r["id"]): r for r in g.all("locations")}

    subj = f"Boarding check-in confirmed — {batch}"
    existing_comms = {
        str(r.get("patient_id")): r
        for r in g.all("communications")
        if r.get("subject") == subj
    }

    processed = []
    skipped = []
    run_status = {}  # track which runs we've already occupied in this pass
    for r in rows:
        rid = str(r["id"])
        run_id = str(r["run_id"])
        patient_id = str(r["patient_id"])
        status = r["run_status"]
        run_patient = str(r["run_patient"]) if r["run_patient"] is not None else None

        is_available = status == "available" and run_status.get(run_id) is None
        already_same = (status == "occupied" and run_patient == patient_id) or run_status.get(run_id) == patient_id
        if not (is_available or already_same):
            skipped.append(r)
            continue

        g.update("boarding_reservations", r["id"], {"status": "checked_in"})
        g.update("boarding_runs", run_id, {
            "status": "occupied",
            "current_patient_id": patient_id,
        })
        run_status[run_id] = patient_id

        if patient_id not in existing_comms:
            p = patients.get(patient_id, {})
            body = (
                f"{p['name']} checked into {r['run_type']} run {r['run_number']} at "
                f"{r['location_name']} on {glib.Gold.dp(r['check_in'])}."
            )
            g.push("communications", {
                "channel": "email",
                "direction": "outbound",
                "subject": subj,
                "body": body,
                "logged_by": "system",
                "occurred_at": ep_ts,
                "owner_id": str(p.get("owner_id")),
                "patient_id": patient_id,
            })
            existing_comms[patient_id] = True

        processed.append(r)

    by_loc = defaultdict(int)
    by_run = defaultdict(int)
    for r in processed:
        by_loc[str(r["location_id"])] += 1
        by_run[r["run_type"]] += 1

    try:
        existing_reports = g.all("ops_reports")
    except RuntimeError:
        existing_reports = []
    for r in existing_reports:
        if r.get("report") == "boarding_checkin_manifest" and r.get("batch_code") == batch:
            g.delete("ops_reports", r["id"])

    g.push("ops_reports", {
        "report": "boarding_checkin_manifest",
        "batch_code": batch,
        "episode_date": ep,
        "checked_in_count": len(processed),
        "skipped_count": len(skipped),
        "by_location": {str(locations.get(loc, {}).get("name", loc)): c for loc, c in by_loc.items()},
        "by_run_type": dict(by_run),
    })

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
