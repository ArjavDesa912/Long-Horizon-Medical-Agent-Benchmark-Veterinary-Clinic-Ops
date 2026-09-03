#!/usr/bin/env python3
"""Gold solution for 001_overdue_vaccine_compliance_flag (run against a FRESH container)."""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_dt = datetime.strptime(ep, "%Y-%m-%d").date()
    for r in g.all("vaccinations"):
        due = glib.Gold.dp(r.get("due_date"))
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
        g.update("vaccinations", r["id"], {"compliance_flag": flag})


if __name__ == "__main__":
    main()
