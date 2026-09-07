#!/usr/bin/env python3
"""Verifier for 091_idempotent_reminder_send (hardmode v2).

Fail-closed, read-only, with dual-path overdue counts and per-patient
earliest-due checks. Catches over-broad mutations of the seed queue and
off-by-one date boundaries.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    v.expect(batch and ep, "nonce missing")

    # ---- dual-path overdue set -------------------------------------------
    vaccs = vlib.fetch_all(v.token, "vaccinations")
    overdue_api: dict = {}
    for r in vaccs:
        due = vlib.dp(r.get("due_date"))
        if due and due < ep:
            pid = str(r.get("patient_id"))
            if pid not in overdue_api or due < overdue_api[pid]:
                overdue_api[pid] = due

    sql_rows = vlib.sql(
        v.token,
        f"SELECT patient_id, MIN(due_date) as earliest "
        f"FROM veterinary_clinic_system_vaccinations "
        f"WHERE due_date < '{ep_ts}' "
        f"GROUP BY patient_id",
    )
    overdue_sql = {str(r["patient_id"]): vlib.dp(r["earliest"]) for r in sql_rows}

    v.expect_equal(len(overdue_sql), len(overdue_api), "overdue patient count: API vs SQL")
    for pid in overdue_api:
        v.expect(pid in overdue_sql, f"patient {pid} overdue in API but not SQL")
        v.expect_equal(overdue_sql[pid], overdue_api[pid], f"earliest due for {pid}: API vs SQL")

    O = len(overdue_api)

    # ---- queue integrity -------------------------------------------------
    seed_q = vlib.seed_rows("reminder_queue")
    live_q = vlib.fetch_all(v.token, "reminder_queue")
    v.expect_equal(len(live_q), len(seed_q) + O, "reminder_queue count")

    seed_q_by_id = {str(r["id"]): r for r in seed_q}
    live_q_by_id = {str(r["id"]): r for r in live_q}
    for rid, s in seed_q_by_id.items():
        live = live_q_by_id.get(rid)
        v.expect(live is not None, f"seed reminder {rid} missing")
        v.expect(vlib.row_eq(live, s, ignore=("updated_at",)), f"seed reminder {rid} changed")

    # One dedupe row per overdue patient.
    for pid, due in overdue_api.items():
        dk = f"vac-{pid}-{batch}"
        matches = [r for r in live_q if str(r.get("patient_id")) == pid and r.get("dedupe_key") == dk]
        v.expect_equal(len(matches), 1, f"patient {pid} expected one dedupe row")
        row = matches[0]
        v.expect_equal(row.get("kind"), "vaccination_due", f"{pid} kind")
        v.expect_equal(row.get("status"), "queued", f"{pid} status")
        v.expect_equal(vlib.dp(row.get("due_date")), due, f"{pid} due_date")
        v.expect_equal(row.get("message"), f"Overdue vaccination reminder {batch}", f"{pid} message")
        v.expect_equal(row.get("queued_by"), "system", f"{pid} queued_by")
        v.expect_equal(vlib.dp(row.get("queued_at")), ep, f"{pid} queued_at")
        v.expect_equal(row.get("dedupe_key"), dk, f"{pid} dedupe_key")

    # No duplicate dedupe keys anywhere.
    all_dks = [r.get("dedupe_key") for r in live_q if r.get("dedupe_key")]
    v.expect_equal(len(all_dks), len(set(all_dks)), "duplicate dedupe keys")

    # ---- ops_reports summary ---------------------------------------------
    reports = [
        r for r in vlib.fetch_all(v.token, "ops_reports")
        if r.get("report") == "vaccination_reminder_batch" and r.get("batch_code") == batch
    ]
    v.expect_equal(len(reports), 1, "ops_reports count")
    rep = reports[0]
    v.expect_equal(rep.get("overdue_patients"), O, "report overdue_patients")
    v.expect(rep.get("queued") in (0, O), "report queued")

    v.check_canaries([
        "appointments", "audit_log", "billing_estimates", "billing_invoices",
        "boarding_daily_log", "boarding_reservations", "boarding_runs",
        "communications", "controlled_substance_log", "fee_schedules", "files",
        "lab_results", "location_transfers", "locations", "medications", "owners",
        "patients", "pharmacy_inventory", "providers", "reminder_templates",
        "vaccinations", "visit_records", "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
