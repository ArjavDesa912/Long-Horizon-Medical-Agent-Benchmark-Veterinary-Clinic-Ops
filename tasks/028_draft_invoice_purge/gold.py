#!/usr/bin/env python3
"""Gold solution for 028_draft_invoice_purge (run against a FRESH container)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glib  # noqa: E402


def main():

    g = glib.Gold()
    for r in g.all("billing_invoices"):
        if r.get("status") == "draft":
            g.delete("billing_invoices", r["id"])



if __name__ == "__main__":
    main()
