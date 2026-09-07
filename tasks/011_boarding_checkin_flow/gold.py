#!/usr/bin/env python3
"""Gold solution for 011_boarding_checkin_flow (hardmode v2)."""
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

    reservations = g.all("boarding_reservations")
    runs = {str(r["id"]): r for r in g.all("boarding_runs")}
    patients = {str(r["id"]): r for r in g.all("patients")}
    locations = {str(r["id"]): r for r in g.all("locations")}
    owners = {str(r["id"]): r for r in g.all("owners")}

    # candidate: reserved with check_in <= ep
    candidates = sorted(
        [r for r in reservations if r.get("status") == "reserved" and glib.Gold.dp(r.get("check_in")) <= ep],
        key=lambda r: (glib.Gold.dp(r.get("check_in")) or "9999", r["id"]),
    )

    subj = f"Boarding check-in confirmed — {batch}"
    existing_comms = {
        str(r.get("patient_id")): r
        for r in g.all("communications")
        if r.get("subject") == subj
    }

    processed = []
    skipped = []
    for r in candidates:
        rid = str(r["id"])
        run_id = str(r.get("run_id"))
        run = runs[run_id]
        patient_id = str(r.get("patient_id"))
        is_available = run.get("status") == "available"
        already_same = str(run.get("current_patient_id")) == patient_id
        if not (is_available or already_same):
            skipped.append(r)
            continue

        # update reservation and run
        g.update("boarding_reservations", r["id"], {"status": "checked_in"})
        g.update("boarding_runs", run_id, {
            "status": "occupied",
            "current_patient_id": patient_id,
        })
        # refresh local run cache
        runs[run_id] = {**run, "status": "occupied", "current_patient_id": patient_id}

        # owner communication
        if patient_id not in existing_comms:
            p = patients.get(patient_id, {})
            owner_id = str(p.get("owner_id"))
            run_type = run.get("run_type")
            run_number = run.get("run_number")
            loc = locations.get(str(r.get("location_id")), {})
            body = (
                f"{p['name']} checked into {run_type} run {run_number} at "
                f"{loc.get('name')} on {glib.Gold.dp(r['check_in'])}."
            )
            g.push("communications", {
                "channel": "email",
                "direction": "outbound",
                "subject": subj,
                "body": body,
                "logged_by": "system",
                "occurred_at": ep_ts,
                "owner_id": owner_id,
                "patient_id": patient_id,
            })
            existing_comms[patient_id] = True

        processed.append(r)

    # manifest
    by_loc = defaultdict(int)
    by_run = defaultdict(int)
    for r in processed:
        by_loc[str(r.get("location_id"))] += 1
        run = runs[str(r.get("run_id"))]
        by_run[run.get("run_type")] += 1

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

    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
