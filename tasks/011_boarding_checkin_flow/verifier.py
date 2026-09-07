#!/usr/bin/env python3
"""Verifier for 011_boarding_checkin_flow (hardmode v2)."""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def _parse_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise vlib.VerifierError(f"expected JSON object, got non-JSON string: {value!r}")
    raise vlib.VerifierError(f"expected JSON object, got {type(value).__name__}")


def _canon_dict(d):
    return json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    v.expect(batch and ep, "nonce missing")

    seed_res = vlib.seed_rows("boarding_reservations")
    live_res = vlib.fetch_all(v.token, "boarding_reservations")
    seed_runs = vlib.seed_rows("boarding_runs")
    live_runs = vlib.fetch_all(v.token, "boarding_runs")
    seed_comms = vlib.seed_rows("communications")
    live_comms = vlib.fetch_all(v.token, "communications")
    patients = {str(r["id"]): r for r in vlib.fetch_all(v.token, "patients")}
    locations = {str(r["id"]): r for r in vlib.fetch_all(v.token, "locations")}

    seed_res_by_id = {str(r["id"]): r for r in seed_res}
    live_res_by_id = {str(r["id"]): r for r in live_res}
    live_runs_by_id = {str(r["id"]): r for r in live_runs}
    seed_comms_by_id = {str(r["id"]): r for r in seed_comms}

    # ----------------------------- Python path: derive processed/skipped
    candidates = sorted(
        [r for r in seed_res if r.get("status") == "reserved" and vlib.dp(r.get("check_in")) <= ep],
        key=lambda r: (vlib.dp(r.get("check_in")) or "9999", r["id"]),
    )

    processed_py = []
    skipped_py = []
    run_state = {}
    for r in candidates:
        rid = str(r["id"])
        run_id = str(r.get("run_id"))
        patient_id = str(r.get("patient_id"))
        run = live_runs_by_id.get(run_id)
        if run is None:
            skipped_py.append(r)
            continue
        status = run.get("status")
        current = run.get("current_patient_id")
        already_occupied = run_state.get(run_id) == patient_id
        if status == "available" or already_occupied or (status == "occupied" and str(current) == patient_id):
            processed_py.append(r)
            run_state[run_id] = patient_id
        else:
            skipped_py.append(r)

    # ----------------------------- SQL path: same counts
    # Candidate ids are scoped explicitly (not re-derived from live r.status)
    # because gold.py flips status reserved->checked_in on the very rows
    # this query needs to find; the run-availability JOIN below is the real
    # independent check being dual-path-verified.
    candidate_ids_sql = ",".join(str(r["id"]) for r in candidates) or "-1"
    sql_proc_rows = vlib.sql(
        v.token,
        "SELECT r.id, r.patient_id, r.run_id, r.location_id, r.check_in, "
        "runs.status, runs.current_patient_id "
        "FROM veterinary_clinic_system_boarding_reservations r "
        "JOIN veterinary_clinic_system_boarding_runs runs ON r.run_id::int = runs.id "
        "WHERE r.id = ANY(ARRAY[%s]) "
        "ORDER BY r.check_in, r.id" % candidate_ids_sql
    )
    processed_sql = []
    run_state_sql = {}
    for r in sql_proc_rows:
        run_id = str(r["run_id"])
        patient_id = str(r["patient_id"])
        status = r["status"]
        current = r["current_patient_id"]
        already = run_state_sql.get(run_id) == patient_id
        if status == "available" or already or (status == "occupied" and str(current) == patient_id):
            processed_sql.append(r)
            run_state_sql[run_id] = patient_id

    v.expect_equal(len(processed_sql), len(processed_py), "processed count: SQL vs Python (dual-path)")
    v.expect_equal(len(sql_proc_rows) - len(processed_sql), len(skipped_py), "skipped count: SQL vs Python (dual-path)")

    # ----------------------------- reservation and run state
    v.expect_equal(len(live_res), len(seed_res), "reservation count")
    v.expect_equal(len(live_runs), len(seed_runs), "run count")

    for rid, seed in seed_res_by_id.items():
        live = live_res_by_id[rid]
        if rid in {str(r["id"]) for r in processed_py}:
            v.expect_equal(live.get("status"), "checked_in", f"reservation {rid} status")
            v.expect(vlib.row_eq(live, seed, ignore=("status", "updated_at")), f"reservation {rid} other fields changed")
        else:
            v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"reservation {rid} changed unexpectedly")

    processed_run_ids = set()
    for r in processed_py:
        rid = str(r["id"])
        run_id = str(r.get("run_id"))
        processed_run_ids.add(run_id)
        live_run = live_runs_by_id[run_id]
        v.expect_equal(live_run.get("status"), "occupied", f"run {run_id} status")
        v.expect_equal(str(live_run.get("current_patient_id")), str(r.get("patient_id")), f"run {run_id} occupant")

    for rid, seed in {str(r["id"]): r for r in seed_runs}.items():
        live = live_runs_by_id[rid]
        if rid in processed_run_ids:
            v.expect(vlib.row_eq(live, seed, ignore=("status", "current_patient_id", "updated_at")), f"run {rid} other fields changed")
        else:
            v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"run {rid} changed unexpectedly")

    # ----------------------------- communications
    subj = f"Boarding check-in confirmed — {batch}"
    new_comms = [r for r in live_comms if r.get("subject") == subj]
    v.expect_equal(len(new_comms), len(processed_py), "communications count")

    for rid, seed in seed_comms_by_id.items():
        live = next((r for r in live_comms if str(r.get("id")) == rid), None)
        v.expect(live is not None and vlib.row_eq(live, seed), f"seeded comm {rid} changed")

    for r in processed_py:
        patient_id = str(r.get("patient_id"))
        matches = [c for c in new_comms if str(c.get("patient_id")) == patient_id]
        v.expect_equal(len(matches), 1, f"patient {patient_id} communication count")
        comm = matches[0]
        p = patients.get(patient_id, {})
        run = live_runs_by_id[str(r.get("run_id"))]
        loc = locations.get(str(r.get("location_id")), {})
        expected_body = (
            f"{p['name']} checked into {run.get('run_type')} run {run.get('run_number')} at "
            f"{loc.get('name')} on {vlib.dp(r['check_in'])}."
        )
        v.expect_equal(comm.get("channel"), "email", f"{patient_id} channel")
        v.expect_equal(comm.get("direction"), "outbound", f"{patient_id} direction")
        v.expect_equal(str(comm.get("owner_id")), str(p.get("owner_id")), f"{patient_id} owner_id")
        v.expect_equal(comm.get("body"), expected_body, f"{patient_id} body")
        v.expect_equal(comm.get("logged_by"), "system", f"{patient_id} logged_by")
        v.expect_equal(vlib.dp(comm.get("occurred_at")), ep, f"{patient_id} occurred_at")

    # ----------------------------- ops report
    reports = vlib.fetch_all(v.token, "ops_reports")
    manifest_rows = [r for r in reports if r.get("report") == "boarding_checkin_manifest" and r.get("batch_code") == batch]
    v.expect_equal(len(manifest_rows), 1, "ops_reports manifest count")
    row = manifest_rows[0]

    by_loc = defaultdict(int)
    by_run = defaultdict(int)
    for r in processed_py:
        by_loc[str(r.get("location_id"))] += 1
        run = live_runs_by_id[str(r.get("run_id"))]
        by_run[run.get("run_type")] += 1

    v.expect_equal(row.get("checked_in_count"), len(processed_py), "checked_in_count")
    v.expect_equal(row.get("skipped_count"), len(skipped_py), "skipped_count")

    row_by_loc = _parse_json(row.get("by_location"))
    for loc_id, count in by_loc.items():
        loc_name = locations.get(loc_id, {}).get("name", loc_id)
        v.expect_equal(row_by_loc.get(loc_name), count, f"by_location {loc_name}")

    row_by_run = _parse_json(row.get("by_run_type"))
    for run_type, count in by_run.items():
        v.expect_equal(row_by_run.get(run_type), count, f"by_run_type {run_type}")

    # ----------------------------- canaries
    v.check_canaries([
        "appointments", "audit_log", "billing_estimates", "billing_invoices",
        "boarding_daily_log", "files", "fee_schedules", "lab_results",
        "location_transfers", "locations", "medications", "owners", "patients",
        "pharmacy_inventory", "providers", "reminder_queue", "reminder_templates",
        "vaccinations", "visit_records", "waitlist"
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
