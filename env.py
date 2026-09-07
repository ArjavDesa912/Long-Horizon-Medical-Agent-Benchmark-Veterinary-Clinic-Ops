"""
Gymnasium-compatible RL environment wrapper for the veterinary_clinic_system
rl-env Docker image (frontend + Stackhouse BaaS + Postgres 15, pre-seeded at build
time).

Upgrades over the original reference implementation (per RL_ENV_FACTORY_PROMPT
Phase 4):

1. Task sets: ``task_id`` selects ``tasks/<task_id>/task.json`` — one env class
   serves the whole suite.
2. Rewards are computed by shelling out to the task's *standalone host-side*
   verifier (``tasks/<task_id>/verifier.py``); reward is 1.0 iff it exits 0.
   No inline reward logic that can drift from the verifier.
3. ``reset()`` injects a fresh per-episode nonce into the collection/field
   named by the task's ``nonce`` config before returning the first
   observation. Verifiers re-read the nonce live, so memorized answers go
   stale every episode.
4. Rewards are always computed against this episode's own mapped BaaS port;
   agent-supplied URLs are never trusted.
5. The collection prefix is derived as ``f"{app_slug}_"`` — never taken from
   the manifest (an older image build reported a doubled underscore).

Only the Python standard library + gymnasium are required: container lifecycle
goes through the ``docker`` CLI (subprocess) and HTTP through urllib.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import gymnasium as gym
from gymnasium import spaces

VALID_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
VALID_USERS = ("verifier", "app_admin")
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_NONCE_COLLECTION_SUFFIX = "ops_meta"
DEFAULT_NONCE_FIELD = "batch_code"
VERIFIER_TIMEOUT_S = 90


def _free_port() -> int:
    """Ask the OS for an unused TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class StackhouseEnv(gym.Env):
    """Gymnasium environment that drives one rl-env container via the Stackhouse REST API."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        app_slug: str = "veterinary_clinic_system",
        task_id: Optional[str] = None,
        image: Optional[str] = None,
        host_app_port: Optional[int] = None,
        host_baas_port: Optional[int] = None,
        auto_remove: bool = True,
        task_path: Optional[str] = None,
        startup_timeout: float = 240.0,
        max_steps: Optional[int] = None,
    ):
        super().__init__()
        self.app_slug = app_slug
        self.task_id = task_id
        self.image = image or f"rl-env/{app_slug}:latest"
        self.host_app_port = host_app_port
        self.host_baas_port = host_baas_port
        self.auto_remove = auto_remove
        self.startup_timeout = startup_timeout

        # container_app_port is discovered from the image's EXPOSE metadata in reset(),
        # since it varies per app (each software gets its own Vite dev-server port).
        self.container_app_port: Optional[int] = None
        self.container_id: Optional[str] = None
        self.manifest: dict[str, Any] = {}
        self._tokens: dict[str, str] = {}
        self._step_count = 0
        self.nonce_value: Optional[str] = None

        # ---- task loading ------------------------------------------------
        resolved_task_path = task_path
        if resolved_task_path is None and task_id is not None:
            resolved_task_path = os.path.join(HERE, "tasks", task_id, "task.json")
        self.task: Optional[dict[str, Any]] = None
        self._task_dir: Optional[str] = None
        self._task_file_hashes: dict[str, str] = {}
        if resolved_task_path and os.path.exists(resolved_task_path):
            with open(resolved_task_path, "r", encoding="utf-8") as f:
                self.task = json.load(f)
            self._task_dir = os.path.dirname(resolved_task_path)
            # Tamper evidence: re-hashed at grading time (Phase 3b threat model).
            for fname in ("task.json", "verifier.py"):
                fpath = os.path.join(self._task_dir, fname)
                if os.path.exists(fpath):
                    self._task_file_hashes[fname] = _sha256(fpath)

        self.max_steps = max_steps or (self.task or {}).get("max_steps") or 50

        # The action is a JSON-describable dict; Gymnasium's Text space needs bounds,
        # so payload is carried as a JSON-encoded string rather than a nested Dict.
        self.action_space = spaces.Dict(
            {
                "method": spaces.Text(min_length=1, max_length=10),
                "endpoint": spaces.Text(min_length=1, max_length=500),
                "payload": spaces.Text(min_length=0, max_length=200_000),
                "as_user": spaces.Text(min_length=1, max_length=20),
            }
        )
        # Observation is the JSON-encoded result of GET /v1/tables, filtered to this
        # app's collections.
        self.observation_space = spaces.Text(min_length=0, max_length=2_000_000)

    # ------------------------------------------------------------------ #
    # Container lifecycle
    # ------------------------------------------------------------------ #

    def _image_exposed_ports(self) -> list[int]:
        result = subprocess.run(
            ["docker", "inspect", self.image, "--format", "{{json .Config.ExposedPorts}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        exposed = json.loads(result.stdout.strip())
        return [int(key.split("/")[0]) for key in exposed]

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.close()  # idempotent: tear down any previous container first

        exposed = self._image_exposed_ports()
        stackhouse_container_port = 9090
        app_candidates = [p for p in exposed if p != stackhouse_container_port]
        if not app_candidates:
            raise RuntimeError(
                f"Could not determine APP_PORT for image {self.image}: "
                f"exposed ports were {exposed}"
            )
        self.container_app_port = app_candidates[0]

        self.host_app_port = self.host_app_port or _free_port()
        self.host_baas_port = self.host_baas_port or _free_port()

        container_name = f"rlenv-{self.app_slug}-{uuid.uuid4().hex[:8]}"
        cmd = ["docker", "run", "-d", "--name", container_name]
        if self.auto_remove:
            cmd.append("--rm")
        cmd += [
            "-p", f"{self.host_app_port}:{self.container_app_port}",
            "-p", f"{self.host_baas_port}:{stackhouse_container_port}",
            self.image,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.container_id = result.stdout.strip()

        self._wait_for_healthy()
        self.manifest = self._read_manifest()
        self._tokens = {}
        self._step_count = 0

        # Some image builds lazily migrate the BaaS app schema after the
        # healthcheck succeeds. Wait until app tables are visible before
        # injecting the nonce or running any verifier/gold.
        prefix = f"{self.app_slug}_"
        token = None
        for _ in range(60):
            token = token or self._login("verifier")
            status, body = self._http("GET", "/v1/tables", token=token)
            if status == 200 and any(t.startswith(prefix) for t in body.get("tables", [])):
                break
            import time
            time.sleep(2)

        # Phase 3a.3 — per-episode nonce injection, before first observation.
        self.nonce_value = self._inject_nonce()

        # The Stackhouse backend can return 503 for a second or two after the first
        # authenticated request; a short settle window prevents gold/verifier races.
        import time
        time.sleep(2)

        observation = self._get_observation()
        info = {"manifest": self.manifest, "nonce": self.nonce_value}
        if self.task:
            info["task_id"] = self.task.get("task_id")
            info["instruction"] = self.task.get("instruction")
        return observation, info

    def _wait_for_healthy(self) -> None:
        deadline = time.time() + self.startup_timeout
        last_error = ""
        while time.time() < deadline:
            probe = subprocess.run(
                ["docker", "exec", self.container_id, "/rl/healthcheck.sh"],
                capture_output=True,
                text=True,
            )
            if probe.returncode == 0:
                return
            last_error = (probe.stdout + probe.stderr).strip()
            time.sleep(2)
        raise TimeoutError(
            f"Container {self.container_id} did not become healthy within "
            f"{self.startup_timeout}s. Last healthcheck output: {last_error!r}"
        )

    def _read_manifest(self) -> dict[str, Any]:
        result = subprocess.run(
            ["docker", "exec", self.container_id, "cat", "/rl/manifest.json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    def close(self):
        if self.container_id is None:
            return
        subprocess.run(["docker", "stop", self.container_id], capture_output=True)
        if not self.auto_remove:
            subprocess.run(["docker", "rm", "-f", self.container_id], capture_output=True)
        self.container_id = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ------------------------------------------------------------------ #
    # Nonce injection (anti-memorization)
    # ------------------------------------------------------------------ #

    def _inject_nonce(self) -> Optional[str]:
        """Upsert a fresh per-episode nonce row into the task's nonce collection.

        The row uses key='episode_state' so repeated resets on the same container
        update rather than duplicate. Tasks that reference the nonce instruct the
        agent to read it from <prefix><nonce.collection> field <nonce.field>.
        """
        if not self.task:
            return None
        nonce_cfg = self.task.get("nonce") or {}
        suffix = nonce_cfg.get("collection", DEFAULT_NONCE_COLLECTION_SUFFIX)
        field = nonce_cfg.get("field", DEFAULT_NONCE_FIELD)
        collection = suffix if suffix.startswith(f"{self.app_slug}_") else f"{self.app_slug}_{suffix}"
        token = f"EP-{secrets.token_hex(4).upper()}"
        now = datetime.now(timezone.utc)
        # The seed data spans Aug/Sep 2026 relative to image build time; a fixed
        # month-end anchor keeps every date-bound task's target set non-empty.
        # Hardmode: jitter ±3 days per episode (Hard Rule 5 — randomize beyond
        # just the nonce) so a boundary count memorized from a prior episode is
        # wrong, not just stale. Still anchored near month-end, not a free
        # random date, so overdue/upcoming windows stay meaningfully populated.
        base_date = datetime(2026, 9, 30, tzinfo=timezone.utc).date()
        jitter_days = secrets.randbelow(7) - 3  # -3..+3
        business_date = (base_date + timedelta(days=jitter_days)).isoformat()
        row = {
            # 'meta_key' not 'key': Stackhouse rejects SQL reserved keywords as
            # filter identifiers (verified: ?key=... -> HTTP 400).
            "meta_key": "episode_state",
            field: token,
            "injected_at": now.isoformat(),
            # Fixed business-date anchor (not wall-clock) so every episode is
            # evaluated against the same calendar that the seed was designed for.
            # ISO-with-time because this Stackhouse build stores bare dates as NULL.
            "episode_date": business_date + "T00:00:00.000Z",
        }
        # Optional per-task randomized parameters (e.g. a markup percentage the
        # instruction references); sampled fresh every episode so memorized
        # constants go stale.
        for extra_field, spec in (nonce_cfg.get("extra_fields") or {}).items():
            lo, hi = int(spec.get("min", 1)), int(spec.get("max", 100))
            row[extra_field] = secrets.randbelow(hi - lo + 1) + lo
        auth = self._login("verifier")
        try:
            status, body = self._http("GET", f"/v1/query/{collection}?meta_key=episode_state&limit=100", token=auth)
            existing = body.get("data", []) if status == 200 else []
            for e in existing:
                self._http("POST", f"/v1/delete/{collection}/{e['id']}", token=auth)
            self._http("POST", f"/v1/push/{collection}", row, token=auth)
        except Exception:
            # Nonce injection failure must not crash reset; verifiers will FAIL
            # closed when they cannot read the nonce, which is the safe outcome.
            return None
        return token

    # ------------------------------------------------------------------ #
    # Stackhouse REST helpers
    # ------------------------------------------------------------------ #

    def _baas_url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.host_baas_port}{path}"

    def _http(self, method: str, path: str, payload: Any = None, token: Optional[str] = None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if isinstance(payload, str):
            data = payload.encode()
        else:
            data = json.dumps(payload).encode() if payload is not None else None
        last_exc = None
        for attempt in range(3):
            req = urllib.request.Request(self._baas_url(path), data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode()
                    status = resp.status
                break
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                status = e.code
                if status >= 500 and attempt < 2:
                    import time
                    time.sleep(1.0 * (attempt + 1))
                    continue
                break
            except (TimeoutError, OSError, urllib.error.URLError) as e:
                last_exc = e
                if attempt < 2:
                    import time
                    time.sleep(1.0 * (attempt + 1))
                    continue
                status, body = 0, str(e)
                break
        else:
            status, body = 0, str(last_exc)
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return status, parsed

    def _login(self, as_user: str) -> Optional[str]:
        if as_user in self._tokens:
            return self._tokens[as_user]
        if as_user == "verifier":
            email = self.manifest.get("verifier_email")
            password = self.manifest.get("verifier_password")
        elif as_user == "app_admin":
            email = self.manifest.get("app_admin_email")
            password = self.manifest.get("app_admin_password")
        else:
            raise ValueError(f"as_user must be one of {VALID_USERS}, got {as_user!r}")
        if not email or not password:
            return None
        status, body = self._http("POST", "/v1/auth/login", {"email": email, "password": password})
        if status != 200:
            return None
        token = body.get("data", {}).get("access_token")
        if token:
            self._tokens[as_user] = token
        return token

    def _get_observation(self) -> str:
        status, body = self._http("GET", "/v1/tables")
        all_tables = body.get("tables", []) if status == 200 else []
        prefix = f"{self.app_slug}_"
        app_tables = [t for t in all_tables if t.startswith(prefix)]
        return json.dumps({"status": status, "collection_prefix": prefix, "tables": app_tables})

    # ------------------------------------------------------------------ #
    # Gymnasium API
    # ------------------------------------------------------------------ #

    def step(self, action: dict[str, Any]):
        method = str(action.get("method", "")).upper()
        endpoint = action.get("endpoint", "")
        payload = action.get("payload")
        as_user = action.get("as_user", "verifier")

        rejection: str | None = None
        status, body = 0, {}
        try:
            if method not in VALID_METHODS:
                raise ValueError(f"method must be one of {VALID_METHODS}, got {method!r}")
            if as_user not in VALID_USERS:
                raise ValueError(f"as_user must be one of {VALID_USERS}, got {as_user!r}")
            if not endpoint.startswith("/"):
                raise ValueError(f"endpoint must be a path starting with '/', got {endpoint!r}")
            if isinstance(payload, str) and payload:
                payload = json.loads(payload)
            token = self._login(as_user)
            status, body = self._http(method, endpoint, payload, token)
        except Exception as e:
            # A malformed action (bad method/user/endpoint shape, a payload
            # that isn't valid JSON, an endpoint with characters urllib
            # rejects -- e.g. http.client.InvalidURL for a stray space, which
            # isn't even a ValueError -- or any other dispatch failure) must
            # not crash the whole rollout. This is the agent's action-dispatch
            # boundary: any way the agent can produce a bad action here is
            # exactly the kind of mistake it should see reflected in
            # reward_reason so it can self-correct next turn, not an
            # exception type we have to keep enumerating one at a time as new
            # mistakes surface. Broad by design, not by accident.
            rejection = f"Action rejected, not sent to Stackhouse: {e}"

        self._step_count += 1
        reward, reward_info = self._compute_reward()
        observation = self._get_observation()
        terminated = reward >= 1.0
        truncated = (not terminated) and self._step_count >= self.max_steps

        if rejection:
            reward_info = {**reward_info, "reward_reason": rejection}

        info = {
            "status_code": status,
            "response": body,
            "as_user": as_user,
            **reward_info,
        }
        return observation, reward, terminated, truncated, info

    def _compute_reward(self) -> tuple[float, dict[str, Any]]:
        """Shell out to the task's standalone host-side verifier (no inline drift).

        Reward is 1.0 iff verifier.py exits 0 against *this episode's own* mapped
        BaaS port. Task-file hashes are re-checked first (tamper evidence).
        """
        if not self.task or not self._task_dir:
            return 0.0, {"reward_reason": "no task loaded (pass task_id=... to __init__)"}

        for fname, expected_hash in self._task_file_hashes.items():
            fpath = os.path.join(self._task_dir, fname)
            if not os.path.exists(fpath) or _sha256(fpath) != expected_hash:
                return 0.0, {"reward_reason": f"task file tampered or missing: {fname}"}

        verifier_path = os.path.join(self._task_dir, "verifier.py")
        if not os.path.exists(verifier_path):
            return 0.0, {"reward_reason": "verifier.py missing for task"}

        env_vars = dict(
            os.environ,
            STACKHOUSE_API_URL=f"http://127.0.0.1:{self.host_baas_port}",
        )
        try:
            result = subprocess.run(
                [sys.executable, verifier_path],
                env=env_vars,
                capture_output=True,
                text=True,
                timeout=VERIFIER_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return 0.0, {"reward_reason": "verifier timed out"}
        except Exception as e:  # fail closed
            return 0.0, {"reward_reason": f"verifier launch failed: {e}"}

        reason = (result.stdout or "").strip().splitlines()
        reward_reason = reason[-1] if reason else (result.stderr or "").strip()[-200:]
        if result.returncode == 0:
            return 1.0, {"reward_reason": reward_reason or "PASS"}
        return 0.0, {"reward_reason": reward_reason or f"verifier exit {result.returncode}"}

    def render(self):
        return None
