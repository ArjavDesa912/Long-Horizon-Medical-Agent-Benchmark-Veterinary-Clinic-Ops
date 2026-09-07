#!/usr/bin/env python3
"""
Shared stdlib-only helpers for veterinary_clinic_system gold solutions.

Gold scripts prove solvability end-to-end: they run against a FRESH container
via the public Stackhouse REST API, exactly the way an agent is expected to.
This module provides the write-side primitives (vlib.py is read-only).

Usage in a gold script:

    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
    import glib

    g = glib.Gold()                       # logs in as verifier (or app_admin)
    owners = g.all("owners")
    ...
    g.push("reminder_queue", {...})
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

STACKHOUSE_API_URL = os.environ.get("STACKHOUSE_API_URL", "http://127.0.0.1:9090").rstrip("/")
PREFIX = "veterinary_clinic_system_"
PAGE = 500


class Gold:
    def __init__(self, email: str = "rl-admin@rl.local", password: str = "RLVerifier2025!"):
        self.url = STACKHOUSE_API_URL
        self.token = self.login(email, password)
        self.steps = 0  # API-call counter -> recorded as par_steps

    # ---------------------------- HTTP ---------------------------- #
    def _http(self, method: str, path: str, payload=None, token=None, retries: int = 5):
        headers = {"Content-Type": "application/json"}
        use_token = token if token is not None else self.token
        if use_token:
            headers["Authorization"] = f"Bearer {use_token}"
        data = json.dumps(payload).encode() if payload is not None else None
        last_code = 0
        for attempt in range(retries + 1):
            req = urllib.request.Request(f"{self.url}{path}", data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = resp.read().decode()
                    return resp.status, (json.loads(body) if body else {})
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                last_code = e.code
                if e.code >= 500 and attempt < retries:
                    import time
                    time.sleep(1.0 * (attempt + 1))
                    continue
                try:
                    return e.code, json.loads(body) if body else {}
                except json.JSONDecodeError:
                    return e.code, {"raw": body}
        return last_code, {}

    def login(self, email: str, password: str) -> str:
        status, body = self._http("POST", "/v1/auth/login", {"email": email, "password": password}, token="")
        token = (body.get("data") or {}).get("access_token") if status == 200 else None
        if not token:
            raise RuntimeError(f"gold login failed for {email} (HTTP {status}): {body}")
        return token

    # ---------------------------- reads ---------------------------- #
    def q(self, collection: str, **params) -> list[dict]:
        coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
        path = f"/v1/query/{coll}"
        if params:
            path += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        self.steps += 1
        status, body = self._http("GET", path)
        if status != 200:
            raise RuntimeError(f"query {coll} -> HTTP {status}: {body}")
        return body.get("data", [])

    def all(self, collection: str, **params) -> list[dict]:
        rows, offset = [], 0
        while True:
            page = self.q(collection, **{**params, "limit": PAGE, "offset": offset})
            rows.extend(page)
            if len(page) < PAGE:
                return rows
            offset += PAGE

    def one(self, collection: str, doc_id) -> dict | None:
        coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
        self.steps += 1
        status, body = self._http("GET", f"/v1/query/{coll}/{doc_id}")
        return body.get("data") if status == 200 else None

    def sql(self, statement: str) -> list[dict]:
        self.steps += 1
        status, body = self._http("POST", "/v1/sql/query", {"query": statement})
        if status != 200:
            raise RuntimeError(f"sql/query -> HTTP {status}: {body}")
        return body.get("data", [])

    # ---------------------------- writes ---------------------------- #
    def push(self, collection: str, doc: dict) -> dict:
        coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
        self.steps += 1
        status, body = self._http("POST", f"/v1/push/{coll}", doc)
        if status not in (200, 201):
            raise RuntimeError(f"push {coll} -> HTTP {status}: {body}")
        return body.get("data", {})

    def update(self, collection: str, doc_id, updates: dict):
        coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
        self.steps += 1
        status, body = self._http("POST", f"/v1/update/{coll}/{doc_id}", updates)
        if status not in (200, 201):
            raise RuntimeError(f"update {coll}/{doc_id} -> HTTP {status}: {body}")

    def delete(self, collection: str, doc_id):
        coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
        self.steps += 1
        status, body = self._http("POST", f"/v1/delete/{coll}/{doc_id}")
        if status not in (200, 201):
            raise RuntimeError(f"delete {coll}/{doc_id} -> HTTP {status}: {body}")

    # ---------------------------- misc ---------------------------- #
    def nonce(self, collection: str = "ops_meta", field: str = "batch_code") -> str:
        """Read the per-episode nonce env.py injects into ops_meta at reset().
        Retries briefly: under concurrent container load, this gold call can
        outrace env.py's nonce-injection write (table not yet created, or the
        row not yet visible)."""
        import time

        last_err: Exception | None = None
        for attempt in range(10):
            try:
                rows = self.q(collection, meta_key="episode_state", limit=1)
            except RuntimeError as e:
                last_err = e
                rows = []
            if rows:
                return str(rows[0][field])
            time.sleep(0.5 * (attempt + 1))
        raise last_err or RuntimeError(f"nonce row missing in {PREFIX}{collection}")

    @staticmethod
    def dp(value) -> str | None:
        """Date-prefix normalizer ('YYYY-MM-DD'); matches vlib.dp semantics."""
        if value is None:
            return None
        s = str(value)
        return s[:10] if len(s) >= 10 else s

    @staticmethod
    def cents(value) -> int:
        """Money -> integer cents; matches vlib.cents semantics."""
        if value is None:
            return 0
        from decimal import Decimal, ROUND_HALF_UP
        return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
