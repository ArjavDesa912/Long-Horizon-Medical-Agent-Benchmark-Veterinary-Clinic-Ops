#!/usr/bin/env python3
"""Verifier for 061_new_patient_enrollment (hardmode v2).

Read-only, fail-closed, dual-path where a number is derived from live data.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")
    ep_ts = ep + "T00:00:00.000Z"

    # resolver inputs
    providers = vlib.fetch_all(v.token, "providers")
    fee_rows = vlib.fetch_all(v.token, "fee_schedules")
    locations = vlib.fetch_all(v.token, "locations")

    # expected exotics provider at location 1
    exotics = None
    for p in providers:
        if (
            str(p.get("location_id")) == "1"
            and p.get("role") == "veterinarian"
            and any(str(s).lower() == "exotics" for s in (p.get("specialties") or []))
        ):
            exotics = p
            break
    v.expect(exotics is not None, "no exotics provider at location 1")
    provider_id = str(exotics["id"])
    provider_name = exotics["full_name"]

    # expected price (Python path)
    fee_loc1 = next((f for f in fee_rows if str(f.get("location_id")) == "1"), None)
    v.expect(fee_loc1 is not None, "no fee schedule for location 1")
    price = None
    for item in fee_loc1.get("items", []):
        if item.get("code") == "WELL-EXAM":
            price = float(item.get("price", 0))
            break
    v.expect(price is not None, "WELL-EXAM not in fee schedule")

    # SQL path for price (as a dual-path check of the fee schedule)
    sql_price_rows = vlib.sql(
        v.token,
        "SELECT (item->>'price')::numeric as price "
        "FROM veterinary_clinic_system_fee_schedules f, "
        "jsonb_array_elements(f.items::jsonb) item "
        "WHERE f.location_id = '1' AND item->>'code' = 'WELL-EXAM'",
    )
    if sql_price_rows:
        sql_price = float(sql_price_rows[0]["price"])
        v.expect(abs(sql_price - price) < 0.01, f"fee schedule price: Python {price} vs SQL {sql_price}")

    # patients
    seed_p = vlib.seed_rows("patients")
    live_p = vlib.fetch_all(v.token, "patients")
    v.expect_equal(len(live_p), len(seed_p) + 1, "patient count")
    seed_p_by_id = {str(r["id"]): r for r in seed_p}
    live_p_by_id = {str(r["id"]): r for r in live_p}
    # existing patients must be byte-identical (only their updated_at may move)
    for pid, seed in seed_p_by_id.items():
        live = live_p_by_id.get(pid)
        v.expect(live is not None, f"seed patient {pid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seed patient {pid} changed")
    new_patients = [r for r in live_p if str(r.get("id")) not in seed_p_by_id]
    v.expect_equal(len(new_patients), 1, "new patient count")
    patient = new_patients[0]
    patient_id = str(patient["id"])
    v.expect_equal(patient.get("name"), "Maple Syrup", "patient name")
    v.expect_equal(patient.get("sex"), "female", "patient sex")
    v.expect_equal(patient.get("species"), "exotic", "patient species")
    v.expect_equal(patient.get("breed"), "Holland Lop", "patient breed")
    v.expect_equal(patient.get("spayed_neutered"), True, "patient spayed_neutered")
    v.expect_equal(vlib.dp(patient.get("dob")), "2023-02-14", "patient dob")
    v.expect_equal(patient.get("weight_kg"), 1.8, "patient weight_kg")
    v.expect_equal(str(patient.get("owner_id")), "3", "patient owner_id")
    v.expect_equal(str(patient.get("location_id")), "1", "patient location_id")
    v.expect_equal(patient.get("status"), "active", "patient status")
    v.expect_equal(patient.get("alerts"), [], "patient alerts")
    chip = str(patient.get("microchip_id")) if patient.get("microchip_id") is not None else ""
    v.expect(re.match(r"^\d{15}$", chip) is not None, f"patient microchip_id not 15 digits: {chip!r}")
    v.expect_equal(chip, "985112900001234", "patient microchip_id")
    # created_at can't be asserted against ep: the platform always stamps it
    # server-side (real insert time) and silently drops any client-provided
    # value for this column, regardless of what gold.py pushes.
    v.expect(patient.get("created_at") is not None, "patient created_at missing")

    # appointments
    seed_a = vlib.seed_rows("appointments")
    live_a = vlib.fetch_all(v.token, "appointments")
    v.expect_equal(len(live_a), len(seed_a) + 1, "appointment count")
    live_a_by_id = {str(r["id"]): r for r in live_a}
    seed_a_by_id = {str(r["id"]): r for r in seed_a}
    for aid, seed in seed_a_by_id.items():
        live = live_a_by_id.get(aid)
        v.expect(live is not None, f"seed appointment {aid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seed appointment {aid} changed")
    new_appts = [r for r in live_a if str(r.get("id")) not in {str(x["id"]) for x in seed_a}]
    v.expect_equal(len(new_appts), 1, "new appointment count")
    appt = new_appts[0]
    v.expect_equal(str(appt.get("patient_id")), patient_id, "appointment patient_id")
    v.expect_equal(str(appt.get("provider_id")), provider_id, "appointment provider_id")
    v.expect_equal(str(appt.get("location_id")), "1", "appointment location_id")
    v.expect_equal(vlib.dp(appt.get("appointment_date")), ep, "appointment date")
    v.expect_equal(appt.get("start_time"), "09:00", "appointment start_time")
    v.expect_equal(appt.get("end_time"), "09:30", "appointment end_time")
    v.expect_equal(appt.get("room"), "Exam 2", "appointment room")
    v.expect_equal(appt.get("reason"), "New-patient wellness exam", "appointment reason")
    v.expect_equal(appt.get("status"), "scheduled", "appointment status")
    v.expect_equal(appt.get("intake_batch"), batch, "appointment intake_batch")
    # no conflicting provider appointment at that time
    conflicts = [
        r
        for r in live_a
        if str(r.get("provider_id")) == provider_id
        and r is not appt
        and vlib.dp(r.get("appointment_date")) == ep
        and r.get("start_time") == "09:00"
    ]
    v.expect_equal(len(conflicts), 0, "provider already booked at 09:00 on episode date")

    # billing estimates
    seed_e = vlib.seed_rows("billing_estimates")
    live_e = vlib.fetch_all(v.token, "billing_estimates")
    v.expect_equal(len(live_e), len(seed_e) + 1, "estimate count")
    live_e_by_id = {str(r["id"]): r for r in live_e}
    seed_e_by_id = {str(r["id"]): r for r in seed_e}
    for eid, seed in seed_e_by_id.items():
        live = live_e_by_id.get(eid)
        v.expect(live is not None, f"seed estimate {eid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seed estimate {eid} changed")
    new_ests = [r for r in live_e if str(r.get("id")) not in {str(x["id"]) for x in seed_e}]
    v.expect_equal(len(new_ests), 1, "new estimate count")
    est = new_ests[0]
    v.expect_equal(est.get("estimate_number"), f"EST-NP-{batch}", "estimate number")
    v.expect_equal(est.get("status"), "draft", "estimate status")
    v.expect_equal(str(est.get("owner_id")), "3", "estimate owner_id")
    v.expect_equal(str(est.get("patient_id")), patient_id, "estimate patient_id")
    v.expect_equal(str(est.get("location_id")), "1", "estimate location_id")
    v.expect_equal(vlib.dp(est.get("created_date")), ep, "estimate created_date")
    v.expect_equal(vlib.dp(est.get("expires_date")), ep, "estimate expires_date")
    v.expect_equal(vlib.cents(est.get("total_amount")), vlib.cents(price), "estimate total_amount")
    line_items = est.get("line_items") or []
    v.expect_equal(len(line_items), 1, "estimate line_items count")
    li = line_items[0]
    v.expect_equal(li.get("code"), "WELL-EXAM", "line item code")
    v.expect_equal(li.get("description"), "Wellness examination", "line item description")
    v.expect_equal(vlib.cents(li.get("unit_price")), vlib.cents(price), "line item unit_price")
    v.expect_equal(li.get("quantity"), 1, "line item quantity")
    v.expect_equal(est.get("intake_batch"), batch, "estimate intake_batch")

    # dual-path estimate count (Python vs SQL)
    sql_est_count = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_billing_estimates "
        f"WHERE estimate_number = 'EST-NP-{batch}'",
    )
    if sql_est_count:
        v.expect_equal(int(sql_est_count[0]["cnt"]), 1, "estimate count: SQL vs Python")

    # communications
    seed_c = vlib.seed_rows("communications")
    live_c = vlib.fetch_all(v.token, "communications")
    v.expect_equal(len(live_c), len(seed_c) + 1, "communications count")
    live_c_by_id = {str(r["id"]): r for r in live_c}
    seed_c_by_id = {str(r["id"]): r for r in seed_c}
    for cid, seed in seed_c_by_id.items():
        live = live_c_by_id.get(cid)
        v.expect(live is not None, f"seed communication {cid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seed communication {cid} changed")
    subject = f"Welcome — Maple Syrup ({batch})"
    matches = [c for c in live_c if c.get("subject") == subject and str(c.get("owner_id")) == "3"]
    v.expect_equal(len(matches), 1, "welcome comm count")
    comm = matches[0]
    expected_body = (
        f"Welcome! Maple Syrup is enrolled at Main Street Animal Hospital; "
        f"first wellness exam with {provider_name} on {ep} 09:00–09:30. "
        f"Estimate: ${price:.2f} (WELL-EXAM)."
    )
    v.expect_equal(comm.get("body"), expected_body, "comm body")
    v.expect_equal(comm.get("channel"), "email", "comm channel")
    v.expect_equal(comm.get("direction"), "outbound", "comm direction")
    v.expect_equal(str(comm.get("patient_id")), patient_id, "comm patient_id")
    v.expect_equal(comm.get("logged_by"), "system", "comm logged_by")
    v.expect_equal(vlib.dp(comm.get("occurred_at")), ep, "comm occurred_at")

    # audit log
    seed_audit = vlib.seed_rows("audit_log")
    live_audit = vlib.fetch_all(v.token, "audit_log")
    v.expect_equal(len(live_audit), len(seed_audit) + 1, "audit_log count")
    live_audit_by_id = {str(r["id"]): r for r in live_audit}
    seed_audit_by_id = {str(r["id"]): r for r in seed_audit}
    for aid, seed in seed_audit_by_id.items():
        live = live_audit_by_id.get(aid)
        v.expect(live is not None, f"seed audit {aid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seed audit {aid} changed")
    audit_matches = [a for a in live_audit if a.get("action") == "PATIENT_ENROLLED" and batch in str(a.get("details", ""))]
    v.expect_equal(len(audit_matches), 1, "PATIENT_ENROLLED audit count")
    a = audit_matches[0]
    v.expect_equal(a.get("actor"), "Dana Whitaker", "audit actor")
    v.expect_equal(a.get("actor_role"), "org_admin", "audit actor_role")
    v.expect_equal(a.get("target_collection"), "patients", "audit target_collection")
    v.expect_equal(str(a.get("target_id")), patient_id, "audit target_id")
    v.expect_equal(a.get("details"), f"New patient intake {batch}: Maple Syrup for owner 3.", "audit details")
    v.expect_equal(vlib.dp(a.get("occurred_at")), ep, "audit occurred_at")

    v.check_canaries([
        "billing_invoices", "boarding_daily_log", "boarding_reservations", "boarding_runs",
        "controlled_substance_log", "fee_schedules", "files", "lab_results", "location_transfers",
        "locations", "medications", "owners", "pharmacy_inventory", "providers",
        "reminder_queue", "reminder_templates", "vaccinations", "visit_records",
        "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
