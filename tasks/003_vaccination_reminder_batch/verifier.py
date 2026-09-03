#!/usr/bin/env python3
"""Verifier for 003_vaccination_reminder_batch.

Compute expected patient set: patients with any vaccination due<episode_date, minus patients with a PRE-EXISTING queued vaccination_due reminder (from snapshot: patient_ids 2 and 5 have queued vaccination_due rows). For each expected patient: exactly one NEW row exists with correct kind/status/queued_by, due_date==min overdue due, message=='<name> is overdue for <type> — call to book a nurse visit.' where <type> is the vaccine_type of that min-due row. Assert seeded 4 rows byte-identical to snapshot, total count == 4+len(expected), and no duplicate new rows per patient.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(ep, "episode_date missing")
    patients = {str(r["id"]): r for r in vlib.fetch_all(v.token, "patients")}
    vaccs = vlib.fetch_all(v.token, "vaccinations")
    queue = vlib.fetch_all(v.token, "reminder_queue")
    seed_q = vlib.seed_rows("reminder_queue")
    existing = set(str(r.get("patient_id")) for r in seed_q if r.get("kind") == "vaccination_due" and r.get("status") == "queued")
    overdue = {}
    for r in vaccs:
        due = vlib.dp(r.get("due_date"))
        if due and due < ep:
            pid = str(r.get("patient_id"))
            if pid not in overdue or due < overdue[pid][0]:
                overdue[pid] = (due, r)
    expected = {pid: (due, r) for pid, (due, r) in overdue.items() if pid not in existing}
    v.expect_equal(len(queue), len(seed_q) + len(expected), "reminder_queue count")
    seed_by_id = {str(r["id"]): r for r in seed_q}
    live_by_id = {str(r["id"]): r for r in queue}
    for rid, seed in seed_by_id.items():
        live = live_by_id.get(rid)
        v.expect(live is not None, f"seeded reminder row {rid} missing")
        v.expect(vlib.row_eq(live, seed), f"seeded reminder row {rid} changed")
    for pid, (due, vr) in expected.items():
        p = patients[pid]
        msg = f"{p['name']} is overdue for {vr['vaccine_type']} — call to book a nurse visit."
        matches = [r for r in queue if str(r.get("patient_id")) == pid and r.get("kind") == "vaccination_due" and r.get("status") == "queued"]
        v.expect_equal(len(matches), 1, f"patient {pid} expected exactly one new reminder row")
        row = matches[0]
        v.expect_equal(vlib.dp(row.get("due_date")), due, f"{pid} due_date")
        v.expect_equal(row.get("kind"), "vaccination_due", f"{pid} kind")
        v.expect_equal(row.get("status"), "queued", f"{pid} status")
        v.expect_equal(row.get("queued_by"), "admin@pawsclinic.com", f"{pid} queued_by")
        v.expect_equal(vlib.dp(row.get("queued_at")), ep, f"{pid} queued_at")
        v.expect_equal(row.get("message"), msg, f"{pid} message")

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_templates', 'vaccinations', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
