#!/usr/bin/env python3
"""Verifier for 091_idempotent_reminder_send.

Compute expected overdue set; assert exactly one row per patient with correct dedupe_key (live nonce); assert no patient has 2 rows with the same dedupe_key; seeded rows unchanged; total == 4 + E.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:

    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    v.expect(batch and ep, "nonce missing")
    vaccs = vlib.fetch_all(v.token, "vaccinations")
    patients = {str(r["id"]): r for r in vlib.fetch_all(v.token, "patients")}
    queue = vlib.fetch_all(v.token, "reminder_queue")
    seed_q = vlib.seed_rows("reminder_queue")
    overdue = {}
    for r in vaccs:
        due = vlib.dp(r.get("due_date"))
        if due and due < ep:
            pid = str(r.get("patient_id"))
            if pid not in overdue or due < overdue[pid][0]:
                overdue[pid] = (due, r)
    expected = set(overdue.keys())
    v.expect_equal(len(queue), len(seed_q) + len(expected), "reminder_queue count")
    seed_q_by_id = {str(r["id"]): r for r in seed_q}
    live_q_by_id = {str(r["id"]): r for r in queue}
    for rid, s in seed_q_by_id.items():
        v.expect(vlib.row_eq(live_q_by_id[rid], s, ignore=("updated_at",)), f"seeded reminder {rid} changed")
    seen = set()
    for pid in expected:
        dk = f"vac-{pid}-{batch}"
        matches = [r for r in queue if r.get("dedupe_key") == dk and str(r.get("patient_id")) == pid]
        v.expect_equal(len(matches), 1, f"patient {pid} expected one dedupe row")
        row = matches[0]
        due, vr = overdue[pid]
        v.expect_equal(row.get("kind"), "vaccination_due", f"{pid} kind")
        v.expect_equal(vlib.dp(row.get("due_date")), due, f"{pid} due_date")
        v.expect_equal(row.get("message"), f"Overdue vaccination reminder {batch}", f"{pid} message")
        v.expect_equal(row.get("status"), "queued", f"{pid} status")
        v.expect_equal(row.get("queued_by"), "system", f"{pid} queued_by")
        v.expect_equal(vlib.dp(row.get("queued_at")), ep, f"{pid} queued_at")
        v.expect_equal(row.get("dedupe_key"), dk, f"{pid} dedupe_key")
        v.expect(dk not in seen, f"duplicate dedupe key {dk}")
        seen.add(dk)

    v.check_canaries(['appointments', 'audit_log', 'billing_estimates', 'billing_invoices', 'boarding_daily_log', 'boarding_reservations', 'boarding_runs', 'communications', 'controlled_substance_log', 'fee_schedules', 'files', 'lab_results', 'location_transfers', 'locations', 'medications', 'owners', 'patients', 'pharmacy_inventory', 'providers', 'reminder_templates', 'vaccinations', 'visit_records', 'waitlist'])


if __name__ == "__main__":
    vlib.run(None, checks)
