#!/usr/bin/env python3
"""Verifier for 002_rabies_booster_due_recompute (hardmode v2).

Recompute canine rabies due dates as administered_date + 1 year, then audit:
reminders, communications, ops_reports, audit_log. Every aggregate is computed
both from raw-row Python filters and from an independent SQL query (dual-path).
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def one_year_after(adm: str) -> str:
    d = datetime.strptime(adm, "%Y-%m-%d").date()
    try:
        nd = d.replace(year=d.year + 1)
    except ValueError:
        nd = d.replace(year=d.year + 1, day=d.day - 1)
    return nd.strftime("%Y-%m-%d")


def checks(v: vlib.Verifier) -> None:
    batch = vlib.get_nonce(v.token)
    ep = vlib.dp(vlib.get_nonce(v.token, field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    end = (ep_dt + timedelta(days=30)).strftime("%Y-%m-%d")
    v.expect(batch and ep, "nonce missing")

    # ------------------------------------------------------------ seed + live
    seed_v = {str(r["id"]): r for r in vlib.seed_rows("vaccinations")}
    live_v = vlib.fetch_all(v.token, "vaccinations")
    patients = {str(r["id"]): r for r in vlib.fetch_all(v.token, "patients")}
    seed_q = vlib.seed_rows("reminder_queue")
    live_q = vlib.fetch_all(v.token, "reminder_queue")
    seed_c = vlib.seed_rows("communications")
    live_c = vlib.fetch_all(v.token, "communications")
    seed_a = vlib.seed_rows("audit_log")
    live_a = vlib.fetch_all(v.token, "audit_log")
    inventory = vlib.fetch_all(v.token, "pharmacy_inventory")
    live_reports = vlib.fetch_all(v.token, "ops_reports")

    # ------------------------------------------------------------ recompute
    live_v_by_id = {str(r["id"]): r for r in live_v}
    expected_due = {}
    total = overdue = due_next_30 = current = 0
    for r in live_v:
        pid = str(r.get("patient_id"))
        p = patients.get(pid)
        seed = seed_v.get(str(r["id"]))
        v.expect(seed is not None, f"vaccination {r.get('id')} missing from snapshot")
        is_target = p is not None and p.get("species") == "canine" and r.get("vaccine_type") == "rabies"
        if is_target:
            adm = vlib.dp(seed.get("administered_date"))
            v.expect(adm, f"administered_date missing for {r['id']}")
            exp = one_year_after(adm)
            expected_due[str(r["id"])] = exp
            v.expect_equal(vlib.dp(r.get("due_date")), exp, f"vaccination {r['id']} due_date")
            v.expect(vlib.row_eq(r, seed, ignore=("due_date", "updated_at")), f"vaccination {r['id']} non-due fields changed")
            total += 1
            if exp < ep:
                overdue += 1
            elif exp <= end:
                due_next_30 += 1
            else:
                current += 1
        else:
            v.expect(vlib.row_eq(r, seed, ignore=("updated_at",)), f"vaccination {r['id']} non-target row changed")

    # Dual-path: target/totals/overdue/due_next_30/current via SQL.
    sql_total_rows = vlib.sql(
        v.token,
        "SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations v "
        "JOIN veterinary_clinic_system_patients p ON v.patient_id = p.id::text "
        "WHERE v.vaccine_type = 'rabies' AND p.species = 'canine'",
    )
    sql_total = int(sql_total_rows[0]["cnt"]) if sql_total_rows else 0
    v.expect_equal(sql_total, total, "total canine rabies: API vs SQL disagree (dual-path)")

    sql_overdue_rows = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations v "
        f"JOIN veterinary_clinic_system_patients p ON v.patient_id = p.id::text "
        f"WHERE v.vaccine_type = 'rabies' AND p.species = 'canine' AND v.due_date < '{ep_ts}'",
    )
    sql_overdue = int(sql_overdue_rows[0]["cnt"]) if sql_overdue_rows else 0
    v.expect_equal(sql_overdue, overdue, "overdue count: API vs SQL disagree (dual-path)")

    end_ts = end + "T23:59:59.999Z"
    sql_due30_rows = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations v "
        f"JOIN veterinary_clinic_system_patients p ON v.patient_id = p.id::text "
        f"WHERE v.vaccine_type = 'rabies' AND p.species = 'canine' "
        f"AND v.due_date >= '{ep_ts}' AND v.due_date <= '{end_ts}'",
    )
    sql_due30 = int(sql_due30_rows[0]["cnt"]) if sql_due30_rows else 0
    v.expect_equal(sql_due30, due_next_30, "due_next_30 count: API vs SQL disagree (dual-path)")

    sql_current_rows = vlib.sql(
        v.token,
        f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_vaccinations v "
        f"JOIN veterinary_clinic_system_patients p ON v.patient_id = p.id::text "
        f"WHERE v.vaccine_type = 'rabies' AND p.species = 'canine' AND v.due_date > '{end_ts}'",
    )
    sql_current = int(sql_current_rows[0]["cnt"]) if sql_current_rows else 0
    v.expect_equal(sql_current, current, "current count: API vs SQL disagree (dual-path)")

    # Expected patients needing attention (new due <= ep+30).
    needs_attention = {}
    for rid, exp in expected_due.items():
        if exp <= end:
            pid = str(live_v_by_id[rid]["patient_id"])
            needs_attention[pid] = min(needs_attention.get(pid, exp), exp)

    # ------------------------------------------------------------ reminder_queue
    seed_q_by_id = {str(r["id"]): r for r in seed_q}
    live_q_by_id = {str(r["id"]): r for r in live_q}
    v.expect_equal(len(live_q), len(seed_q) + len(needs_attention), "reminder_queue count")
    for rid, seed in seed_q_by_id.items():
        live = live_q_by_id.get(rid)
        v.expect(live is not None, f"seeded reminder {rid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seeded reminder {rid} changed")

    for pid, due in needs_attention.items():
        p = patients[pid]
        matches = [r for r in live_q if str(r.get("patient_id")) == pid and r.get("kind") == "vaccination_due" and r.get("status") == "queued"]
        v.expect_equal(len(matches), 1, f"patient {pid} reminder count")
        row = matches[0]
        v.expect_equal(vlib.dp(row.get("due_date")), due, f"{pid} due_date")
        v.expect_equal(row.get("kind"), "vaccination_due", f"{pid} kind")
        v.expect_equal(row.get("status"), "queued", f"{pid} status")
        v.expect_equal(row.get("queued_by"), "admin@pawsclinic.com", f"{pid} queued_by")
        v.expect_equal(vlib.dp(row.get("queued_at")), ep, f"{pid} queued_at")
        msg = f"{p['name']} rabies booster due {due} — call to book a nurse visit."
        v.expect_equal(row.get("message"), msg, f"{pid} message")

    # Dual-path reminder count by SQL (filtered to the expected patient set).
    if needs_attention:
        pid_list = ", ".join(f"'{pid}'" for pid in needs_attention)
        sql_rem_count_rows = vlib.sql(
            v.token,
            f"SELECT COUNT(*) as cnt FROM veterinary_clinic_system_reminder_queue "
            f"WHERE kind = 'vaccination_due' AND status = 'queued' "
            f"AND patient_id IN ({pid_list})",
        )
        sql_rem_count = int(sql_rem_count_rows[0]["cnt"]) if sql_rem_count_rows else 0
    else:
        sql_rem_count = 0
    v.expect_equal(sql_rem_count, len(needs_attention), "reminder count: API vs SQL disagree (dual-path)")

    # ------------------------------------------------------------ communications
    seed_c_by_id = {str(r["id"]): r for r in seed_c}
    live_c_by_id = {str(r["id"]): r for r in live_c}
    v.expect_equal(len(live_c), len(seed_c) + len(needs_attention), "communications count")
    for rid, seed in seed_c_by_id.items():
        live = live_c_by_id.get(rid)
        v.expect(live is not None, f"seeded comm {rid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seeded comm {rid} changed")

    subj = f"Rabies booster recompute {batch}"
    for pid, due in needs_attention.items():
        p = patients[pid]
        matches = [r for r in live_c if r.get("subject") == subj and str(r.get("patient_id")) == pid]
        v.expect_equal(len(matches), 1, f"patient {pid} comm count")
        row = matches[0]
        v.expect_equal(str(row.get("owner_id")), str(p.get("owner_id")), f"{pid} owner_id")
        v.expect_equal(row.get("channel"), "email", f"{pid} channel")
        v.expect_equal(row.get("direction"), "outbound", f"{pid} direction")
        v.expect_equal(row.get("body"), f"{p['name']}'s rabies booster is now due by {due} as of {ep}.", f"{pid} body")
        v.expect_equal(row.get("logged_by"), "system", f"{pid} logged_by")
        v.expect_equal(vlib.dp(row.get("occurred_at")), ep, f"{pid} occurred_at")

    # ------------------------------------------------------------ ops_reports
    reports = [r for r in live_reports if r.get("batch_code") == batch]
    audit_rows = [r for r in reports if r.get("report") == "rabies_recompute_audit"]
    cov_rows = [r for r in reports if r.get("report") == "rabies_inventory_coverage"]
    v.expect_equal(len(audit_rows), 1, "rabies_recompute_audit row count")
    v.expect_equal(len(cov_rows), 1, "rabies_inventory_coverage row count")

    ar = audit_rows[0]
    v.expect_equal(ar.get("total_canine_rabies"), total, "total_canine_rabies")
    v.expect_equal(ar.get("recomputed_overdue"), overdue, "recomputed_overdue")
    v.expect_equal(ar.get("recomputed_due_next_30"), due_next_30, "recomputed_due_next_30")
    v.expect_equal(ar.get("recomputed_current"), current, "recomputed_current")

    on_hand = sum(
        int(r.get("quantity_on_hand", 0))
        for r in inventory
        if isinstance(r.get("item_name"), str) and r["item_name"].startswith("Rabies vaccine 1yr")
    )
    cr = cov_rows[0]
    v.expect_equal(cr.get("vaccine_type"), "rabies", "coverage vaccine_type")
    v.expect_equal(cr.get("item_name"), "Rabies vaccine 1yr", "coverage item_name")
    v.expect_equal(cr.get("due_next_30"), due_next_30, "coverage due_next_30")
    v.expect_equal(cr.get("on_hand"), on_hand, "coverage on_hand")
    v.expect_equal(cr.get("coverage_gap"), max(0, due_next_30 - on_hand), "coverage coverage_gap")

    # Dual-path on_hand via SQL.
    sql_on_hand_rows = vlib.sql(
        v.token,
        "SELECT COALESCE(SUM(quantity_on_hand), 0) as total "
        "FROM veterinary_clinic_system_pharmacy_inventory "
        "WHERE item_name LIKE 'Rabies vaccine 1yr%'",
    )
    sql_on_hand = int(sql_on_hand_rows[0]["total"]) if sql_on_hand_rows else 0
    v.expect_equal(sql_on_hand, on_hand, "on_hand: API vs SQL disagree (dual-path)")

    # ------------------------------------------------------------ audit_log
    seed_a_by_id = {str(r["id"]): r for r in seed_a}
    live_a_by_id = {str(r["id"]): r for r in live_a}
    v.expect_equal(len(live_a), len(seed_a) + 1, "audit_log count")
    for rid, seed in seed_a_by_id.items():
        live = live_a_by_id.get(rid)
        v.expect(live is not None, f"seeded audit {rid} missing")
        v.expect(vlib.row_eq(live, seed, ignore=("updated_at",)), f"seeded audit {rid} changed")

    batch_audit = [r for r in live_a if r.get("action") == "RABIES_RECOMPUTE_BATCH" and r.get("target_id") == batch]
    v.expect_equal(len(batch_audit), 1, "RABIES_RECOMPUTE_BATCH audit row count")
    row = batch_audit[0]
    v.expect_equal(row.get("actor"), "system", "audit actor")
    v.expect_equal(row.get("actor_role"), "system", "audit actor_role")
    v.expect_equal(row.get("target_collection"), "vaccinations", "audit target_collection")
    v.expect_equal(vlib.dp(row.get("occurred_at")), ep, "audit occurred_at")

    # ------------------------------------------------------------ canary
    v.check_canaries([
        "appointments", "billing_estimates", "billing_invoices", "boarding_daily_log",
        "boarding_reservations", "boarding_runs", "controlled_substance_log",
        "fee_schedules", "files", "lab_results", "location_transfers", "locations",
        "medications", "owners", "patients", "pharmacy_inventory", "providers",
        "reminder_templates", "visit_records", "waitlist",
    ])


if __name__ == "__main__":
    vlib.run(None, checks)
