#!/usr/bin/env python3
"""Gold solution for 011_boarding_checkin_flow (run against a FRESH container)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    reserved = g.all("boarding_reservations", status="reserved")
    target = min(reserved, key=lambda r: glib.Gold.dp(r.get("check_in")) or "9999")
    g.update("boarding_reservations", target["id"], {"status": "checked_in"})
    g.update("boarding_runs", target["run_id"], {
        "status": "occupied",
        "current_patient_id": str(target["patient_id"]),
    })
    print(f"gold done in {g.steps} API calls")


if __name__ == "__main__":
    main()
