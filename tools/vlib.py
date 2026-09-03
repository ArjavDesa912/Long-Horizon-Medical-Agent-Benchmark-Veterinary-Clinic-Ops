#!/usr/bin/env python3
"""
Shared stdlib-only helpers for veterinary_clinic_system task verifiers.

Every verifier imports this module (sys.path insert of <env_root>/tools) and
builds its checks from these primitives:

- login / query / qone / sql        -- read-only VibeDB access (GET + login only)
- fetch_all                         -- paginated full-collection read
- dp(value)                         -- date-prefix normalizer ('YYYY-MM-DD')
- cents(value)                      -- money comparison in integer cents
- canon / sha                       -- canonical JSON + sha256 for canary checks
- load_snapshot()                   -- host-side seed snapshot (originals)
- get_nonce()                       -- live per-episode nonce value
- Verifier                          -- fail-closed assertion runner

Verifier contract (RL_ENV_FACTORY_PROMPT Phase 3a):
  * read-only grading (GETs + login only -- never POST/PUT/DELETE)
  * fail closed: any exception, timeout, or unexpected shape => FAIL
  * first-failing-assertion detail cap
  * exits 0 + prints PASS, or exits 1 + prints FAIL: <reason>
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

VIBEDB_URL = os.environ.get("VIBEDB_URL", "http://127.0.0.1:8080").rstrip("/")
PREFIX = "veterinary_clinic_system_"
SNAPSHOT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_expectations", "seed_snapshot.json")
)
HTTP_TIMEOUT = 20
PAGE = 500


class VerifierError(Exception):
    """Internal control-flow exception; caught by run() -> FAIL."""


# --------------------------------------------------------------------- HTTP

def _http(method: str, path: str, payload=None, token: str | None = None, retries: int = 5):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode() if payload is not None else None
    last_code = 0
    for attempt in range(retries + 1):
        req = urllib.request.Request(f"{VIBEDB_URL}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
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


def login(email: str, password: str) -> str:
    status, body = _http("POST", "/v1/auth/login", {"email": email, "password": password})
    token = (body.get("data") or {}).get("access_token") if status == 200 else None
    if not token:
        raise VerifierError(f"login failed for {email} (HTTP {status})")
    return token


def query(token: str, collection: str, params: dict | None = None) -> list[dict]:
    """Single-page query. collection may be given with or without the app prefix."""
    coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
    path = f"/v1/query/{coll}"
    if params:
        path += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    status, body = _http("GET", path, token=token)
    if status == 404 and body.get("error", {}).get("code") == "TABLE_NOT_FOUND":
        return []
    if status != 200:
        raise VerifierError(f"query {coll} -> HTTP {status}")
    data = body.get("data")
    if not isinstance(data, list):
        raise VerifierError(f"query {coll} returned unexpected shape")
    return data


def fetch_all(token: str, collection: str, params: dict | None = None) -> list[dict]:
    """Paginated read of a full collection (honors extra equality filters)."""
    rows: list[dict] = []
    offset = 0
    while True:
        page = query(token, collection, {**(params or {}), "limit": PAGE, "offset": offset})
        rows.extend(page)
        if len(page) < PAGE:
            return rows
        offset += PAGE


def qone(token: str, collection: str, doc_id) -> dict | None:
    coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
    status, body = _http("GET", f"/v1/query/{coll}/{doc_id}", token=token)
    if status != 200:
        return None
    return body.get("data")


def sql(token: str, statement: str) -> list[dict]:
    """Read-only SQL escape hatch. Verifiers must only ever pass SELECTs."""
    if not statement.strip().lower().startswith("select"):
        raise VerifierError("verifier attempted non-SELECT SQL (read-only grading violated)")
    status, body = _http("POST", "/v1/sql/query", {"query": statement}, token=token)
    if status != 200:
        raise VerifierError(f"sql/query -> HTTP {status}")
    data = body.get("data")
    return data if isinstance(data, list) else []


# --------------------------------------------------------------- normalize

def dp(value) -> str | None:
    """Date-prefix normalizer: 'YYYY-MM-DD' from any ISO-ish value; None-safe."""
    if value is None:
        return None
    s = str(value)
    return s[:10] if len(s) >= 10 else s


def cents(value) -> int:
    """Money -> integer cents with banker's-safe rounding via Decimal."""
    from decimal import Decimal, ROUND_HALF_UP

    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def canon(rows: list[dict]) -> str:
    """Canonical JSON dump of a row set: sorted by id, keys sorted, None-stable."""
    def key(r):
        rid = r.get("id")
        return (0, int(rid)) if isinstance(rid, int) or (isinstance(rid, str) and rid.isdigit()) else (1, str(rid))

    return json.dumps(sorted(rows, key=key), sort_keys=True, separators=(",", ":"), default=str)


def sha(rows: list[dict]) -> str:
    return hashlib.sha256(canon(rows).encode()).hexdigest()


def _deep_eq(a, b) -> bool:
    """Recursive equality that tolerates int/float numeric equivalence."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_deep_eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_deep_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b


def row_eq(live: dict, seed: dict, ignore: tuple = ()) -> bool:
    """Compare live row to seed, ignoring listed keys and any extra keys in live
    that are null (e.g. schema-widened columns). Ignores id type differences.
    """
    a = {k: v for k, v in live.items() if k not in ignore and (k in seed or v is not None)}
    b = {k: v for k, v in seed.items() if k not in ignore}
    for d in (a, b):
        if "id" in d:
            d["id"] = str(d["id"])
    return _deep_eq(a, b)


# --------------------------------------------------------------- snapshot

_snapshot_cache: dict | None = None


def load_snapshot() -> dict:
    """Host-side seed snapshot captured from the fresh image (originals + canary hashes)."""
    global _snapshot_cache
    if _snapshot_cache is None:
        if not os.path.exists(SNAPSHOT_PATH):
            raise VerifierError(f"seed snapshot missing at {SNAPSHOT_PATH}")
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            _snapshot_cache = json.load(f)
    return _snapshot_cache


def seed_rows(collection: str) -> list[dict]:
    """Original (pre-episode) rows of a collection from the host-side snapshot."""
    snap = load_snapshot()
    coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
    entry = (snap.get("collections") or {}).get(coll)
    if entry is None:
        raise VerifierError(f"snapshot has no collection {coll}")
    return entry.get("rows", [])


def canary_hash(collection: str) -> str:
    snap = load_snapshot()
    coll = collection if collection.startswith(PREFIX) else f"{PREFIX}{collection}"
    entry = (snap.get("collections") or {}).get(coll)
    if entry is None:
        raise VerifierError(f"snapshot has no collection {coll}")
    return entry.get("sha256", "")


# ------------------------------------------------------------------ nonce

def get_nonce(token: str, collection: str = "ops_meta", field: str = "batch_code") -> str:
    """Read the live per-episode nonce injected by env.reset()."""
    rows = query(token, collection, {"meta_key": "episode_state", "limit": 1})
    if not rows:
        raise VerifierError(f"nonce row missing in {PREFIX}{collection}")
    value = rows[0].get(field)
    if not value:
        raise VerifierError(f"nonce field {field} empty in {PREFIX}{collection}")
    return str(value)


# -------------------------------------------------------------- assertions

class Verifier:
    """Fail-closed assertion runner. Usage:

        v = Verifier(task)
        v.check_canaries(["owners", "locations"])   # untouched collections intact
        v.expect(cond, "reason if not cond")        # first failure wins
        ...
        v.finish()                                   # prints PASS / FAIL + exit code
    """

    def __init__(self, task: dict):
        self.task = task
        self.token: str | None = None

    def connect(self) -> "Verifier":
        self.token = login(self.task["verifier_email"], self.task["verifier_password"])
        return self

    def expect(self, condition: bool, reason: str):
        if not condition:
            raise VerifierError(reason)

    def expect_equal(self, actual, expected, label: str):
        if actual != expected:
            raise VerifierError(f"{label}: expected {expected!r}, found {actual!r}")

    def expect_cents(self, actual, expected, label: str):
        if cents(actual) != cents(expected):
            raise VerifierError(f"{label}: expected {cents(expected)} cents, found {cents(actual)} cents")

    def check_canaries(self, collections: list[str]):
        """Byte-identity of pre-existing collections outside the blast radius."""
        for coll in collections:
            live = fetch_all(self.token, coll)
            live_hash = sha(live)
            want = canary_hash(coll)
            self.expect(
                live_hash == want,
                f"canary violated: {PREFIX}{coll} was modified outside the task's blast radius",
            )

    def finish(self) -> int:
        print("PASS")
        return 0


def run(task_path: str | None, checks):
    """Standard fail-closed entrypoint for every verifier.

        if __name__ == "__main__":
            vlib.run(None, my_checks)   # my_checks(v: Verifier) -> None
    """
    try:
        default_task = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "task.json")
        path = task_path or (sys.argv[1] if len(sys.argv) > 1 else default_task)
        with open(path, "r", encoding="utf-8") as f:
            task = json.load(f)
        v = Verifier(task).connect()
        checks(v)
        sys.exit(v.finish())
    except VerifierError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:  # fail closed on anything unexpected
        print(f"FAIL: verifier error ({type(e).__name__}: {e})")
        sys.exit(1)
