#!/usr/bin/env python3
"""Verifier for 003_vaccination_reminder_batch (hardmode v2).

Overdue patients, one reminder + one email per newly queued patient,
per-vaccine-type report, audit log. Dual-path verification for all aggregates.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    v.expect(batch and ep, "nonce missing")

    # ------------------------------------------------------------ seed + live
    patients = {str(r["id"]): r for r in vlib.fetch_all(v.token, "patients")}
    vaccs = vlib.fetch_all(v.token, "vaccinations")
    seed_q = vlib.seed_rows("reminder_queue")
    live_q = vlib.fetch_all(v.token, "reminder_queue")
    seed_c = vlib.seed_rows("communications")
    live_c = vlib.fetch_all(v.token, "communications")
    seed_a = vlib.seed_rows("audit_log")
    live_a = vlib.fetch_all(v.token, "audit_log")
    live_reports = vlib.fetch_all(v.token, "ops_reports")

    # ------------------------------------------------------------ expected set
    seed_queued_pids = {
        str(r.get("patient_id"))
        for r in seed_q
        if r.get("kind") == "vaccination_due" and r.get("status") == "queued"
    }

    overdue = {}
    for r in vaccs:
        due = vlib.dp(r.get("due_date"))
        if due and due < ep:
            pid = str(r.get("patient_id"))
            cand = (due, r.get("vaccine_type"), r)
            if pid not in overdue or cand[:2] < overdue[pid][:2]:
                overdue[pid] = cand

    expected = {pid: (due, vt, r) for pid, (due, vt, r) in overdue.items() if pid not in seed_queued_pids}
    counts = Counter(vt for _, (_, vt, _) in expected.items())

    # Dual-path: SQL GROUP BY vaccine_type on the batch's reminder_queue rows.
    sql_batch_q = vlib.sql(
        v.token,
        f"SELECT vaccine_type, COUNT(*) as cnt FROM veterinary_clinic_system_reminder_queue "
        f"WHERE kind = 'vaccination_due' AND status = 'queued' AND batch_code = '{batch}' "
        f"GROUP BY vaccine_type",
    )
    sql_counts = {r["vaccine_type"]: int(r["cnt"]) for r in sql_batch_q}
    for vt, cnt in counts.items():
        v.expect_equal(sql_counts.get(vt, 0), cnt, f"{vt} count: API vs SQL disagree (dual-path)")
    sql_total = sum(sql_counts.values())
    v.expect_equal(sql_total, len(expected), "total reminder count: API vs SQL disagree (dual-path)")

    # Dual-path: total overdue patients.
    sql_overdue_rows = vlib.sql(
        v.token,
        f"SELECT COUNT(DISTINCT patient_id) as cnt FROM veterinary_clinic_system_vaccinations "
        f"WHERE due_date < '{ep_ts}'",
    )
    sql_overdue = int(sql_overdue_rows[0]["cnt"]) if sql_overdue_rows else 0
    # Distinct overdue patients includes those with existing queued reminders.
    all_overdue_pids = set(overdue.keys())
    v.expect_equal(sql_overdue, len(all_overdue_pids), "distinct overdue patient count: API vs SQL disagree (dual-path)")

    # ------------------------------------------------------------ reminder_queue
    seed_q_by_id = {str(r["id"]): r for r in seed_q}
    live_q_by_id = {str(r["id"]): r for r in live_q}
    v.expect_equal(len(live_q), len(seed_q) + len(expected), "reminder_queue count")
    for rid, seed in seed_q_by_id.items():
        live = live_q_by_id.get(rid)
        v.expect(live is not None, f"seeded reminder {rid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seeded reminder {rid} changed")

    subj = f"Vaccination reminder {batch}"
    new_q = [r for r in live_q if str(r.get("id")) not in seed_q_by_id and r.get("kind") == "vaccination_due"]
    v.expect_equal(len(new_q), len(expected), "new reminder row count")
    seen = set()
    for r in new_q:
        pid = str(r.get("patient_id"))
        v.expect(pid in expected, f"unexpected reminder for patient {pid}")
        seen.add(pid)
        due, vt, _ = expected[pid]
        p = patients[pid]
        v.expect_equal(vlib.dp(r.get("due_date")), due, f"{pid} due_date")
        v.expect_equal(r.get("vaccine_type"), vt, f"{pid} vaccine_type")
        v.expect_equal(r.get("batch_code"), batch, f"{pid} batch_code")
        v.expect_equal(r.get("kind"), "vaccination_due", f"{pid} kind")
        v.expect_equal(r.get("status"), "queued", f"{pid} status")
        v.expect_equal(r.get("queued_by"), "admin@pawsclinic.com", f"{pid} queued_by")
        v.expect_equal(vlib.dp(r.get("queued_at")), ep, f"{pid} queued_at")
        v.expect_equal(r.get("message"), f"{p['name']} is overdue for {vt} — call to book a nurse visit.", f"{pid} message")
    v.expect_equal(len(seen), len(expected), "reminder patient coverage")

    # ------------------------------------------------------------ communications
    seed_c_by_id = {str(r["id"]): r for r in seed_c}
    live_c_by_id = {str(r["id"]): r for r in live_c}
    v.expect_equal(len(live_c), len(seed_c) + len(expected), "communications count")
    for rid, seed in seed_c_by_id.items():
        live = live_c_by_id.get(rid)
        v.expect(live is not None, f"seeded comm {rid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seeded comm {rid} changed")

    new_c = [r for r in live_c if str(r.get("id")) not in seed_c_by_id and r.get("subject") == subj]
    v.expect_equal(len(new_c), len(expected), "new communication count")
    seen = set()
    for r in new_c:
        pid = str(r.get("patient_id"))
        v.expect(pid in expected, f"unexpected comm for patient {pid}")
        seen.add(pid)
        due, vt, _ = expected[pid]
        p = patients[pid]
        v.expect_equal(str(r.get("owner_id")), str(p.get("owner_id")), f"{pid} owner_id")
        v.expect_equal(r.get("channel"), "email", f"{pid} channel")
        v.expect_equal(r.get("direction"), "outbound", f"{pid} direction")
        v.expect_equal(r.get("body"), f"{p['name']} is overdue for {vt} as of {ep}.", f"{pid} body")
        v.expect_equal(r.get("logged_by"), "system", f"{pid} logged_by")
        v.expect_equal(vlib.dp(r.get("occurred_at")), ep, f"{pid} occurred_at")
    v.expect_equal(len(seen), len(expected), "communication patient coverage")

    # ------------------------------------------------------------ ops_reports
    reports = [r for r in live_reports if r.get("batch_code") == batch and r.get("report") == "vaccination_reminder_batch"]
    v.expect_equal(len(reports), len(counts) + 1, "ops_reports row count")
    by_vt = {r.get("vaccine_type"): r for r in reports}
    for vt in sorted(counts):
        row = by_vt.get(vt)
        v.expect(row is not None, f"missing ops_report for {vt}")
        v.expect_equal(row.get("reminder_count"), counts[vt], f"{vt} reminder_count")
    all_row = by_vt.get("ALL")
    v.expect(all_row is not None, "missing ALL ops_report row")
    v.expect_equal(all_row.get("reminder_count"), len(expected), "ALL reminder_count")

    # ------------------------------------------------------------ audit_log
    seed_a_by_id = {str(r["id"]): r for r in seed_a}
    live_a_by_id = {str(r["id"]): r for r in live_a}
    v.expect_equal(len(live_a), len(seed_a) + 1, "audit_log count")
    for rid, seed in seed_a_by_id.items():
        live = live_a_by_id.get(rid)
        v.expect(live is not None, f"seeded audit {rid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seeded audit {rid} changed")

    batch_audit = [r for r in live_a if r.get("action") == "VACCINATION_REMINDER_BATCH" and r.get("target_id") == batch]
    v.expect_equal(len(batch_audit), 1, "VACCINATION_REMINDER_BATCH audit row count")
    row = batch_audit[0]
    v.expect_equal(row.get("actor"), "system", "audit actor")
    v.expect_equal(row.get("actor_role"), "system", "audit actor_role")
    v.expect_equal(row.get("target_collection"), "reminder_queue", "audit target_collection")
    v.expect_equal(vlib.dp(row.get("occurred_at")), ep, "audit occurred_at")

    # ------------------------------------------------------------ canary
    v.check_canaries([
        "appointments", "billing_estimates", "billing_invoices", "boarding_daily_log",
        "boarding_reservations", "boarding_runs", "controlled_substance_log",
        "fee_schedules", "files", "lab_results", "location_transfers", "locations",
        "medications", "owners", "patients", "pharmacy_inventory", "providers",
        "reminder_templates", "vaccinations", "visit_records", "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
