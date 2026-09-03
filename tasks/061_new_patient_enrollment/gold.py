#!/usr/bin/env python3
"""Gold solution for 061_new_patient_enrollment (run against a FRESH container)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():
    g = glib.Gold()
    ep = glib.Gold.dp(g.nonce(field="episode_date"))
    ep_ts = ep + "T00:00:00.000Z"
    g.push("patients", {
        "name": "Maple Syrup",
        "sex": "female",
        "species": "exotic",
        "breed": "Holland Lop",
        "spayed_neutered": True,
        "dob": "2023-02-14T00:00:00.000Z",
        "weight_kg": 1.8,
        "owner_id": "3",
        "location_id": "1",
        "status": "active",
        "alerts": [],
        "microchip_id": "985112900001",
    })


if __name__ == "__main__":
    main()
