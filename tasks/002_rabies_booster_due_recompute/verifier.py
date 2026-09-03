#!/usr/bin/env python3
"""Verifier for 002_rabies_booster_due_recompute.

Fetch vaccinations + patients. For each vaccination with vaccine_type=='rabies' whose patient species=='canine': expected due = dp(administered_date)+1yr (same month/day; use dateutil-free arithmetic via datetime with year+1, guarding Feb 29 -> Feb 28). Assert dp(due_date)==expected. Assert all other vaccination rows byte-identical to snapshot (strip nothing — these rows must be unmodified; compare via canon of non-target rows vs snapshot non-target rows). Assert count 60.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(ep, "episode_date missing")
    patients = {str(r["id"]): r for r in vlib.fetch_all(v.token, "patients")}
    seed_by_id = {str(r["id"]): r for r in vlib.seed_rows("vaccinations")}
    live = vlib.fetch_all(v.token, "vaccinations")
    v.expect_equal(len(live), len(seed_by_id), "vaccination count")
    for row in live:
        seed = seed_by_id.get(str(row["id"]))
        v.expect(seed is not None, f"vaccination id {row['id']} missing from snapshot")
        is_target = (row.get("vaccine_type") == "rabies" and
                     patients.get(str(row.get("patient_id")), {}).get("species") == "canine")
        if is_target:
            adm = vlib.dp(seed.get("administered_date"))
            v.expect(adm, f"administered_date missing for {row['id']}")
            from datetime import datetime
            d = datetime.strptime(adm, "%Y-%m-%d").date()
            try:
                nd = d.replace(year=d.year + 1)
            except ValueError:
                nd = d.replace(year=d.year + 1, day=d.day - 1)
            exp = nd.strftime("%Y-%m-%dT00:00:00.000Z")
            v.expect_equal(vlib.dp(row.get("due_date")), vlib.dp(exp), f"vaccination {row['id']} due_date")
            v.expect(vlib.row_eq(row, seed, ignore=("due_date", "updated_at")), f"vaccination {row['id']} non-due fields changed")
        else:
            v.expect(vlib.row_eq(row, seed, ignore=("updated_at",)), f"vaccination {row['id']} non-target row changed")

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_queue', 'reminder_templates', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
