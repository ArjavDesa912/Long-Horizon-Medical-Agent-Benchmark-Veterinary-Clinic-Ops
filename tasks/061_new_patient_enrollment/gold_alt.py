#!/usr/bin/env python3
"""Alternate gold solution for 061_new_patient_enrollment.

Reaches the same end-state via SQL-first lookups for provider and fee schedule,
and writes the records in a different order.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    batch = g.nonce()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    if not ep:
        raise RuntimeError("episode_date missing from nonce")
    ep_ts = ep + "T00:00:00.000Z"

    owner_id = "3"
    location_id = "1"
    new_name = "Maple Syrup"

    # SQL-first provider resolution: fetch location-1 veterinarians, then filter
    provider_rows = g.sql(
        f"SELECT id, full_name, specialties, exam_rooms "
        f"FROM veterinary_clinic_system_providers "
        f"WHERE location_id = '{location_id}' AND role = 'veterinarian'"
    )
    provider = None
    for p in provider_rows:
        specs = json.loads(p["specialties"]) if isinstance(p["specialties"], str) else (p["specialties"] or [])
        if any(str(s).lower() == "exotics" for s in specs):
            provider = p
            break
    if not provider:
        raise RuntimeError("no exotics veterinarian at location 1")
    provider_id = str(provider["id"])
    provider_name = provider["full_name"]
    room = "Exam 2"

    # SQL-first fee schedule lookup
    fee_rows = g.sql(
        f"SELECT items "
        f"FROM veterinary_clinic_system_fee_schedules "
        f"WHERE location_id = '{location_id}'"
    )
    if not fee_rows:
        raise RuntimeError("no fee schedule for location 1")
    items = json.loads(fee_rows[0]["items"]) if isinstance(fee_rows[0]["items"], str) else fee_rows[0]["items"]
    price = None
    for item in items:
        if item.get("code") == "WELL-EXAM":
            price = float(item.get("price", 0))
            break
    if price is None:
        raise RuntimeError("WELL-EXAM not found in fee schedule")

    # patient (idempotent by owner+name)
    existing = g.all("patients", owner_id=owner_id, name=new_name)
    if existing:
        patient = existing[0]
    else:
        patient = g.push(
            "patients",
            {
                "name": new_name,
                "sex": "female",
                "species": "exotic",
                "breed": "Holland Lop",
                "spayed_neutered": True,
                "dob": "2023-02-14T00:00:00.000Z",
                "weight_kg": 1.8,
                "owner_id": owner_id,
                "location_id": location_id,
                "status": "active",
                "alerts": [],
                "microchip_id": "985112900001234",
                "created_at": ep_ts,
            },
        )
    patient_id = str(patient.get("id"))

    # write bundle in a different order: audit, comm, estimate, appointment, patient already done
    existing_audit = [
        a
        for a in g.all("audit_log")
        if a.get("action") == "PATIENT_ENROLLED" and batch in str(a.get("details", ""))
    ]
    if not existing_audit:
        g.push(
            "audit_log",
            {
                "actor": "Dana Whitaker",
                "actor_role": "org_admin",
                "action": "PATIENT_ENROLLED",
                "target_collection": "patients",
                "target_id": patient_id,
                "details": f"New patient intake {batch}: Maple Syrup for owner {owner_id}.",
                "occurred_at": ep_ts,
            },
        )

    subject = f"Welcome — Maple Syrup ({batch})"
    existing_comm = [c for c in g.all("communications") if c.get("subject") == subject]
    if not existing_comm:
        body = (
            f"Welcome! Maple Syrup is enrolled at Main Street Animal Hospital; "
            f"first wellness exam with {provider_name} on {ep} 09:00–09:30. "
            f"Estimate: ${price:.2f} (WELL-EXAM)."
        )
        g.push(
            "communications",
            {
                "channel": "email",
                "direction": "outbound",
                "subject": subject,
                "body": body,
                "owner_id": owner_id,
                "patient_id": patient_id,
                "logged_by": "system",
                "occurred_at": ep_ts,
            },
        )

    existing_est = [e for e in g.all("billing_estimates") if e.get("intake_batch") == batch]
    if not existing_est:
        g.push(
            "billing_estimates",
            {
                "estimate_number": f"EST-NP-{batch}",
                "status": "draft",
                "owner_id": owner_id,
                "patient_id": patient_id,
                "location_id": location_id,
                "created_date": ep_ts,
                "expires_date": ep_ts,
                "total_amount": price,
                "line_items": [
                    {
                        "code": "WELL-EXAM",
                        "description": "Wellness examination",
                        "quantity": 1,
                        "unit_price": price,
                    }
                ],
                "intake_batch": batch,
            },
        )

    existing_appt = [a for a in g.all("appointments") if a.get("intake_batch") == batch]
    if not existing_appt:
        g.push(
            "appointments",
            {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "location_id": location_id,
                "appointment_date": ep_ts,
                "start_time": "09:00",
                "end_time": "09:30",
                "room": room,
                "reason": "New-patient wellness exam",
                "status": "scheduled",
                "intake_batch": batch,
            },
        )

    print(f"gold_alt done in {g.steps} API calls")


if __name__ == "__main__":
    main()
