#!/usr/bin/env python3
"""Verifier for 028_draft_invoice_purge.

Assert no invoice with status 'draft' remains; assert all non-draft invoices byte-identical to snapshot; count == 26 - (draft count in snapshot, 1).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    seed_inv = vlib.seed_rows("billing_invoices")
    live_inv = vlib.fetch_all(v.token, "billing_invoices")
    draft_count = sum(1 for r in seed_inv if r.get("status") == "draft")
    v.expect_equal(len(live_inv), len(seed_inv) - draft_count, "invoice count")
    live_by_id = {str(r["id"]): r for r in live_inv}
    seed_by_id = {str(r["id"]): r for r in seed_inv}
    for rid, seed in seed_by_id.items():
        if seed.get("status") == "draft":
            v.expect(str(rid) not in live_by_id, f"draft invoice {rid} still present")
        else:
            v.expect(vlib.row_eq(live_by_id[rid], seed, ignore=("updated_at",)), f"invoice {rid} changed unexpectedly")

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_queue', 'reminder_templates', 'vaccinations', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
