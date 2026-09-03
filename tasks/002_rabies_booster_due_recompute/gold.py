#!/usr/bin/env python3
"""Gold solution for 002_rabies_booster_due_recompute (run against a FRESH container)."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    patients = {str(r["id"]): r for r in g.all("patients")}
    for r in g.all("vaccinations"):
        if r.get("vaccine_type") == "rabies" and patients.get(str(r.get("patient_id")), {}).get("species") == "canine":
            adm = glib.Gold.dp(r.get("administered_date"))
            d = datetime.strptime(adm, "%Y-%m-%d").date()
            try:
                nd = d.replace(year=d.year + 1)
            except ValueError:
                nd = d.replace(year=d.year + 1, day=d.day - 1)
            exp = nd.strftime("%Y-%m-%dT00:00:00.000Z")
            g.update("vaccinations", r["id"], {"due_date": exp})


if __name__ == "__main__":
    main()
