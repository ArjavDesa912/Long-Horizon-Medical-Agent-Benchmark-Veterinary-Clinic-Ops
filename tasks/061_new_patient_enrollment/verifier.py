#!/usr/bin/env python3
"""Verifier for 061_new_patient_enrollment.

Assert exactly one new patient with exact fields; microchip regex ^985112900001$ (15 digits, 985 prefix); count 31; seeded 30 byte-identical.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")
    seed = vlib.seed_rows("patients")
    live = vlib.fetch_all(v.token, "patients")
    v.expect_equal(len(live), len(seed) + 1, "patient count")
    seed_by_id = {str(r["id"]): r for r in seed}
    new = [r for r in live if str(r["id"]) not in seed_by_id]
    v.expect_equal(len(new), 1, "new patient count")
    row = new[0]
    v.expect_equal(row.get("name"), "Maple Syrup", "name")
    v.expect_equal(row.get("sex"), "female", "sex")
    v.expect_equal(row.get("species"), "exotic", "species")
    v.expect_equal(row.get("breed"), "Holland Lop", "breed")
    v.expect_equal(row.get("spayed_neutered"), True, "spayed_neutered")
    v.expect_equal(vlib.dp(row.get("dob")), "2023-02-14", "dob")
    v.expect_equal(row.get("weight_kg"), 1.8, "weight_kg")
    v.expect_equal(row.get("owner_id"), "3", "owner_id")
    v.expect_equal(row.get("location_id"), "1", "location_id")
    v.expect_equal(row.get("status"), "active", "status")
    v.expect_equal(row.get("alerts"), [], "alerts")
    v.expect_equal(row.get("microchip_id"), "985112900001", "microchip_id")
    v.expect(row.get("created_at") is not None, "created_at missing")

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'pharmacy_inventory', 'providers', 'reminder_queue', 'reminder_templates', 'vaccinations', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
