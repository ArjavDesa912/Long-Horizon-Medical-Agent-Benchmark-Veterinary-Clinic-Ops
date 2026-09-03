#!/usr/bin/env python3
"""Verifier for 001_overdue_vaccine_compliance_flag.

Read episode_date via get_nonce(field='episode_date'), dp() it. Fetch all vaccinations (60 rows). For each row compute expected flag from dp(due_date): due<ep -> 'overdue'; ep<=due<=ep+7d -> 'due_soon'; else 'current'. Assert every row's compliance_flag equals expected (report first mismatch with row id). Assert row count still 60 and all non-flag fields byte-identical to snapshot rows (compare canon of rows with compliance_flag stripped vs snapshot).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(ep, "episode_date missing from ops_meta")
    from datetime import datetime, timedelta
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    seed_by_id = {str(r["id"]): r for r in vlib.seed_rows("vaccinations")}
    live = vlib.fetch_all(v.token, "vaccinations")
    v.expect_equal(len(live), len(seed_by_id), "vaccination count")
    live_by_id = {str(r["id"]): r for r in live}
    for rid, seed in seed_by_id.items():
        row = live_by_id.get(rid)
        v.expect(row is not None, f"vaccination id {rid} missing")
        due = vlib.dp(row.get("due_date"))
        if due is None:
            flag = "current"
        else:
            due_dt = datetime.strptime(due, "%Y-%m-%d").date()
            if due_dt < ep_dt:
                flag = "overdue"
            elif due_dt <= ep_dt + timedelta(days=7):
                flag = "due_soon"
            else:
                flag = "current"
        v.expect_equal(row.get("compliance_flag"), flag, f"vaccination {rid} compliance_flag")
        v.expect(vlib.row_eq(row, seed, ignore=("compliance_flag", "updated_at")), f"vaccination {rid} non-flag fields changed")

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_queue', 'reminder_templates', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
