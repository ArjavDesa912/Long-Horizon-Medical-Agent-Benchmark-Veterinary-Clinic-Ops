#!/usr/bin/env python3
"""Verifier for 011_boarding_checkin_flow.

Expected end-state: the 'reserved' reservation with the earliest check_in is
'checked_in', and its run is 'occupied' with current_patient_id equal to that
reservation's patient. All other reservations and runs byte-identical to seed.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import vlib  # noqa: E402


def checks(v: vlib.Verifier) -> None:
    seed_res = {str(r["id"]): r for r in vlib.seed_rows("boarding_reservations")}
    seed_runs = {str(r["id"]): r for r in vlib.seed_rows("boarding_runs")}
    live_res = {str(r["id"]): r for r in vlib.fetch_all(v.token, "boarding_reservations")}
    live_runs = {str(r["id"]): r for r in vlib.fetch_all(v.token, "boarding_runs")}

    v.expect_equal(len(live_res), len(seed_res), "reservation count")
    v.expect_equal(len(live_runs), len(seed_runs), "run count")

    reserved = [r for r in seed_res.values() if r.get("status") == "reserved"]
    v.expect(bool(reserved), "snapshot has no reserved reservations (stale snapshot)")
    target = min(reserved, key=lambda r: vlib.dp(r.get("check_in")) or "9999")
    tid, run_id = str(target["id"]), str(target["run_id"])

    v.expect_equal(live_res[tid].get("status"), "checked_in", f"reservation {tid} status")
    v.expect_equal(live_runs[run_id].get("status"), "occupied", f"run {run_id} status")
    v.expect_equal(
        str(live_runs[run_id].get("current_patient_id")), str(target["patient_id"]),
        f"run {run_id} occupant",
    )

    for rid, seed in seed_res.items():
        if rid == tid:
            continue
        v.expect(vlib.canon([live_res[rid]]) == vlib.canon([seed]), f"reservation {rid} modified out of scope")
    for rid, seed in seed_runs.items():
        if rid == run_id:
            continue
        v.expect(vlib.canon([live_runs[rid]]) == vlib.canon([seed]), f"run {rid} modified out of scope")


if __name__ == "__main__":
    vlib.run(None, checks)
