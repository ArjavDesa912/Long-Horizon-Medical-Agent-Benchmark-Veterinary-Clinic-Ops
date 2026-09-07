#!/usr/bin/env python3
"""Verifier for 001_overdue_vaccine_compliance_flag (hardmode v2).

Every aggregate (totals, by-species, by-location, stale reminders) is derived two
independent ways — raw-row Python filter and SQL GROUP BY/COUNT — and both must
agree with each other and with the ops_reports row the agent wrote.
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def _flag(due: str | None, ep: str, soon_end: str) -> str:
    if due is None:
        return "current"
    if due < ep:
        return "overdue"
    if due <= soon_end:
        return "due_soon"
    return "current"


def _parse_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise vlib.VerifierError(f"expected JSON object, got non-JSON string: {value!r}")
    raise vlib.VerifierError(f"expected JSON object, got {type(value).__name__}")


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    ep_ts = ep + "T00:00:00.000Z"
    soon_end = (ep_dt + timedelta(days=7)).strftime("%Y-%m-%d")
    soon_ts = soon_end + "T00:00:00.000Z"

    # ------------------------------------------------------------------ loads
    patients = {str(r["id"]): r for r in vlib.fetch_all(v.token, "patients")}
    locations = {str(r["id"]): r for r in vlib.fetch_all(v.token, "locations")}
    vaccs = vlib.fetch_all(v.token, "vaccinations")
    queue = vlib.fetch_all(v.token, "reminder_queue")
    seed_vaccs = vlib.seed_rows("vaccinations")

    seed_by_id = {str(r["id"]): r for r in seed_vaccs}
    live_by_id = {str(r["id"]): r for r in vaccs}
    v.expect_equal(len(live_by_id), len(seed_by_id), "vaccination count")

    # --------------------------------------------------- Python path: counts
    py_counts = {"overdue": 0, "due_soon": 0, "current": 0}
    py_by_species = defaultdict(lambda: {"overdue": 0, "due_soon": 0, "current": 0})
    py_by_location = defaultdict(lambda: {"overdue": 0, "due_soon": 0, "current": 0})
    py_by_patient_flag = defaultdict(lambda: {"overdue": 0, "due_soon": 0, "current": 0})

    for r in vaccs:
        rid = str(r["id"])
        seed = seed_by_id.get(rid)
        v.expect(seed is not None, f"vaccination {rid} not in seed snapshot")

        due = vlib.dp(r.get("due_date"))
        flag = _flag(due, ep, soon_end)
        v.expect_equal(r.get("compliance_flag"), flag, f"vaccination {rid} compliance_flag")
        v.expect(vlib.row_eq(r, seed, ignore=("compliance_flag", "updated_at")), f"vaccination {rid} non-flag fields changed")

        py_counts[flag] += 1
        py_by_patient_flag[str(r.get("patient_id"))][flag] += 1

        patient = patients.get(str(r.get("patient_id")), {})
        species = patient.get("species")
        if species:
            py_by_species[species][flag] += 1

        loc = locations.get(str(patient.get("location_id")), {})
        loc_name = loc.get("name")
        if loc_name:
            py_by_location[loc_name][flag] += 1

    total = len(vaccs)
    overdue = py_counts["overdue"]
    due_soon = py_counts["due_soon"]
    current = py_counts["current"]
    v.expect_equal(overdue + due_soon + current, total, "flag counts sum to total")
    expected_pct = round(100.0 * current / total, 1) if total else 0.0

    # ------------------------------------------------ stale reminders (Python)
    py_stale = 0
    for q in queue:
        if q.get("kind") == "vaccination_due" and q.get("status") == "queued":
            pid = str(q.get("patient_id"))
            c = py_by_patient_flag.get(pid, {})
            if c.get("overdue", 0) == 0 and c.get("due_soon", 0) == 0:
                py_stale += 1

    # --------------------------------------------------- SQL path: counts
    sql_total = int(vlib.sql(v.token, "SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations")[0]["cnt"])
    sql_overdue = int(vlib.sql(v.token, f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations WHERE due_date < '{ep_ts}'")[0]["cnt"])
    sql_due_soon = int(vlib.sql(v.token, f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations WHERE due_date >= '{ep_ts}' AND due_date <= '{soon_ts}'")[0]["cnt"])
    sql_current = total - sql_overdue - sql_due_soon

    v.expect_equal(sql_total, total, "total: SQL vs Python disagree (dual-path)")
    v.expect_equal(sql_overdue, overdue, "overdue: SQL vs Python disagree (dual-path)")
    v.expect_equal(sql_due_soon, due_soon, "due_soon: SQL vs Python disagree (dual-path)")
    v.expect_equal(sql_current, current, "current: SQL vs Python disagree (dual-path)")

    # --------------------------------------------- SQL path: by species
    sql_species_rows = vlib.sql(
        v.token,
        "SELECT p.species, "
        "SUM(CASE WHEN v.due_date < '%s' THEN 1 ELSE 0 END) as overdue, "
        "SUM(CASE WHEN v.due_date >= '%s' AND v.due_date <= '%s' THEN 1 ELSE 0 END) as due_soon, "
        "SUM(CASE WHEN v.due_date > '%s' THEN 1 ELSE 0 END) as current "
        "FROM veterinary_clinic_system_vaccinations v "
        "JOIN veterinary_clinic_system_patients p ON v.patient_id::int = p.id "
        "GROUP BY p.species" % (ep_ts, ep_ts, soon_ts, soon_ts)
    )
    sql_by_species = {
        r["species"]: {
            "overdue": int(r["overdue"]),
            "due_soon": int(r["due_soon"]),
            "current": int(r["current"]),
        }
        for r in sql_species_rows
    }
    v.expect_equal(sql_by_species, dict(py_by_species), "breakdown_by_species: SQL vs Python disagree (dual-path)")

    # --------------------------------------------- SQL path: by location
    sql_location_rows = vlib.sql(
        v.token,
        "SELECT l.name, "
        "SUM(CASE WHEN v.due_date < '%s' THEN 1 ELSE 0 END) as overdue, "
        "SUM(CASE WHEN v.due_date >= '%s' AND v.due_date <= '%s' THEN 1 ELSE 0 END) as due_soon, "
        "SUM(CASE WHEN v.due_date > '%s' THEN 1 ELSE 0 END) as current "
        "FROM veterinary_clinic_system_vaccinations v "
        "JOIN veterinary_clinic_system_patients p ON v.patient_id::int = p.id "
        "JOIN veterinary_clinic_system_locations l ON p.location_id::int = l.id "
        "GROUP BY l.name" % (ep_ts, ep_ts, soon_ts, soon_ts)
    )
    sql_by_location = {
        r["name"]: {
            "overdue": int(r["overdue"]),
            "due_soon": int(r["due_soon"]),
            "current": int(r["current"]),
        }
        for r in sql_location_rows
    }
    v.expect_equal(sql_by_location, dict(py_by_location), "breakdown_by_location: SQL vs Python disagree (dual-path)")

    # --------------------------------------------- SQL path: stale reminders
    sql_stale = int(vlib.sql(
        v.token,
        "SELECT COUNT(*) as cnt FROM ("
        "SELECT q.patient_id FROM veterinary_clinic_system_reminder_queue q "
        "WHERE q.kind = 'vaccination_due' AND q.status = 'queued' "
        "EXCEPT "
        "SELECT DISTINCT v.patient_id FROM veterinary_clinic_system_vaccinations v "
        f"WHERE v.due_date < '{ep_ts}' OR (v.due_date >= '{ep_ts}' AND v.due_date <= '{soon_ts}')"
        ") t"
    )[0]["cnt"])
    v.expect_equal(sql_stale, py_stale, "stale_reminder_count: SQL vs Python disagree (dual-path)")

    # -------------------------------------------------- ops_reports row
    try:
        reports = vlib.fetch_all(v.token, "ops_reports")
    except vlib.VerifierError:
        reports = []
    matching = [r for r in reports if r.get("report") == "vaccination_compliance_snapshot" and r.get("batch_code") == batch]
    v.expect_equal(len(matching), 1, "ops_reports row count for this batch")
    row = matching[0]

    v.expect_equal(row.get("total_vaccinations"), total, "report total_vaccinations")
    v.expect_equal(row.get("overdue_count"), overdue, "report overdue_count")
    v.expect_equal(row.get("due_soon_count"), due_soon, "report due_soon_count")
    v.expect_equal(row.get("current_count"), current, "report current_count")
    v.expect_equal(row.get("compliance_pct"), expected_pct, "report compliance_pct")
    v.expect_equal(row.get("stale_reminder_count"), py_stale, "report stale_reminder_count")

    row_species = _parse_json(row.get("breakdown_by_species"))
    v.expect_equal(row_species, dict(py_by_species), "report breakdown_by_species")
    row_location = _parse_json(row.get("breakdown_by_location"))
    v.expect_equal(row_location, dict(py_by_location), "report breakdown_by_location")

    # Ensure no extra ops_reports rows for this batch
    for r in reports:
        if r.get("report") == "vaccination_compliance_snapshot" and r.get("batch_code") == batch:
            if str(r.get("id")) != str(row.get("id")):
                raise vlib.VerifierError("multiple ops_reports rows for this batch")

    # ------------------------------------------------------------- canaries
    v.check_canaries([
        "appointments", "audit_log", "billing_estimates", "billing_invoices",
        "boarding_daily_log", "boarding_reservations", "boarding_runs", "communications",
        "controlled_substance_log", "fee_schedules", "files", "lab_results",
        "location_transfers", "locations", "medications", "owners",
        "pharmacy_inventory", "providers", "reminder_queue", "reminder_templates",
        "visit_records", "waitlist"
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
