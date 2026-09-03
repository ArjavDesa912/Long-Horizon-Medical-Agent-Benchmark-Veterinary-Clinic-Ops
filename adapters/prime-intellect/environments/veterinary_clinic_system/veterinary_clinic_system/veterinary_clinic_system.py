"""
Prime Intellect (verifiers-spec) adapter for the veterinary_clinic_system RL env.

Ports the container lifecycle (build/run/healthcheck/nonce-injection/teardown)
from ../../../../../env.py verbatim rather than reinventing it, and wires it
into verifiers' vf.StatefulToolEnv: one tool (call_api) lets the model issue
REST calls against the live container; the reward function shells out to the
task's standalone verifier.py exactly like env.py's _compute_reward does.

Only the 10 "open" tasks (task.json + gold.py + verifier.py all present) are
usable here — the other 90 ship task.json + REDTEAM.md only in this public
sample, so load_environment() filters to tasks that actually have a
verifier.py on disk. See ../../../../../README.md.
"""
from __future__ import annotations

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
from datetime import datetime, timezone
from typing import Any, Optional

import verifiers as vf
from datasets import Dataset

HERE = os.path.dirname(os.path.abspath(__file__))
# This package lives 5 levels under the sample repo root when run in-place
# (adapters/prime-intellect/environments/veterinary_clinic_system/veterinary_clinic_system/).
# Once published as a standalone wheel it won't sit next to tasks/ any more,
# so VETCLINIC_REPO_ROOT lets a deployment point at wherever tasks/ actually is.
REPO_ROOT = os.environ.get(
    "VETCLINIC_REPO_ROOT",
    os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..")),
)
TASKS_DIR = os.path.join(REPO_ROOT, "tasks")
VERIFIER_TIMEOUT_S = 90
APP_SLUG = "veterinary_clinic_system"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Container:
    """Ported from ../../../../../env.py's VibeDBEnv container lifecycle."""

    def __init__(self, image: str = f"rl-env/{APP_SLUG}:latest", startup_timeout: float = 240.0):
        self.image = image
        self.startup_timeout = startup_timeout
        self.container_id: Optional[str] = None
        self.host_baas_port: Optional[int] = None
        self.manifest: dict[str, Any] = {}
        self._tokens: dict[str, str] = {}

    def start(self) -> None:
        exposed = self._image_exposed_ports()
        app_candidates = [p for p in exposed if p != 8080]
        if not app_candidates:
            raise RuntimeError(f"Could not determine APP_PORT for image {self.image}: exposed={exposed}")
        host_app_port = _free_port()
        self.host_baas_port = _free_port()
        name = f"rlenv-{APP_SLUG}-{uuid.uuid4().hex[:8]}"
        cmd = [
            "docker", "run", "-d", "--rm", "--name", name,
            "-p", f"{host_app_port}:{app_candidates[0]}",
            "-p", f"{self.host_baas_port}:8080",
            self.image,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.container_id = result.stdout.strip()
        self._wait_healthy()
        self.manifest = json.loads(
            subprocess.run(["docker", "exec", self.container_id, "cat", "/rl/manifest.json"],
                            capture_output=True, text=True, check=True).stdout
        )
        prefix = f"{APP_SLUG}_"
        token = None
        for _ in range(60):
            token = token or self.login("verifier")
            status, body = self.http("GET", "/v1/tables", token=token)
            if status == 200 and any(t.startswith(prefix) for t in body.get("tables", [])):
                break
            time.sleep(2)
        time.sleep(2)  # settle window, matches env.py

    def _image_exposed_ports(self) -> list[int]:
        result = subprocess.run(
            ["docker", "inspect", self.image, "--format", "{{json .Config.ExposedPorts}}"],
            capture_output=True, text=True, check=True,
        )
        exposed = json.loads(result.stdout.strip())
        return [int(k.split("/")[0]) for k in exposed]

    def _wait_healthy(self) -> None:
        deadline = time.time() + self.startup_timeout
        last_error = ""
        while time.time() < deadline:
            probe = subprocess.run(["docker", "exec", self.container_id, "/rl/healthcheck.sh"],
                                    capture_output=True, text=True)
            if probe.returncode == 0:
                return
            last_error = (probe.stdout + probe.stderr).strip()
            time.sleep(2)
        raise TimeoutError(f"Container {self.container_id} unhealthy after {self.startup_timeout}s: {last_error!r}")

    def inject_nonce(self, task: dict[str, Any]) -> Optional[str]:
        nonce_cfg = task.get("nonce") or {}
        suffix = nonce_cfg.get("collection", "ops_meta")
        field = nonce_cfg.get("field", "batch_code")
        collection = suffix if suffix.startswith(f"{APP_SLUG}_") else f"{APP_SLUG}_{suffix}"
        token_val = f"EP-{secrets.token_hex(4).upper()}"
        row = {
            "meta_key": "episode_state",
            field: token_val,
            "injected_at": datetime.now(timezone.utc).isoformat(),
            "episode_date": "2026-09-30T00:00:00.000Z",
        }
        for extra_field, spec in (nonce_cfg.get("extra_fields") or {}).items():
            lo, hi = int(spec.get("min", 1)), int(spec.get("max", 100))
            row[extra_field] = secrets.randbelow(hi - lo + 1) + lo
        auth = self.login("verifier")
        try:
            status, body = self.http("GET", f"/v1/query/{collection}?meta_key=episode_state&limit=100", token=auth)
            for e in (body.get("data", []) if status == 200 else []):
                self.http("POST", f"/v1/delete/{collection}/{e['id']}", token=auth)
            self.http("POST", f"/v1/push/{collection}", row, token=auth)
        except Exception:
            return None
        return token_val

    def http(self, method: str, path: str, payload: Any = None, token: Optional[str] = None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = payload.encode() if isinstance(payload, str) else (json.dumps(payload).encode() if payload is not None else None)
        status, body, last_exc = 0, "", None
        for attempt in range(3):
            req = urllib.request.Request(f"http://127.0.0.1:{self.host_baas_port}{path}", data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body, status = resp.read().decode(), resp.status
                break
            except urllib.error.HTTPError as e:
                body, status = e.read().decode(), e.code
                if status >= 500 and attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                break
            except (TimeoutError, OSError, urllib.error.URLError) as e:
                last_exc = e
                if attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                status, body = 0, str(e)
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return status, parsed

    def login(self, as_user: str) -> Optional[str]:
        if as_user in self._tokens:
            return self._tokens[as_user]
        email = self.manifest.get(f"{as_user}_email")
        password = self.manifest.get(f"{as_user}_password")
        if not email or not password:
            return None
        status, body = self.http("POST", "/v1/auth/login", {"email": email, "password": password})
        token = body.get("data", {}).get("access_token") if status == 200 else None
        if token:
            self._tokens[as_user] = token
        return token

    def stop(self) -> None:
        if self.container_id:
            subprocess.run(["docker", "stop", self.container_id], capture_output=True)
            self.container_id = None


def _load_open_task_ids() -> list[str]:
    """Only tasks with a verifier.py on disk are gradable in this public sample."""
    if not os.path.isdir(TASKS_DIR):
        raise RuntimeError(f"tasks/ not found at {TASKS_DIR}; set VETCLINIC_REPO_ROOT")
    ids = []
    for name in sorted(os.listdir(TASKS_DIR)):
        if os.path.exists(os.path.join(TASKS_DIR, name, "verifier.py")) and os.path.exists(os.path.join(TASKS_DIR, name, "task.json")):
            ids.append(name)
    return ids


def _build_dataset(task_ids: list[str]) -> Dataset:
    rows = []
    for task_id in task_ids:
        with open(os.path.join(TASKS_DIR, task_id, "task.json"), encoding="utf-8") as f:
            task = json.load(f)
        rows.append({"question": task["instruction"], "answer": "", "info": json.dumps({"task_id": task_id})})
    return Dataset.from_list(rows)


def call_api(method: str, endpoint: str, payload: str = "", as_user: str = "verifier",
             base_url: str = "", token_verifier: str = "", token_app_admin: str = "") -> str:
    """Issue one REST call against the running app's VibeDB API.

    method: GET/POST/PUT/PATCH/DELETE. endpoint: a path starting with '/',
    e.g. '/v1/query/veterinary_clinic_system_owners?limit=5'. payload: JSON
    string body for writes, or ''. as_user: 'verifier' or 'app_admin'.
    """
    token = token_verifier if as_user == "verifier" else token_app_admin
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = payload.encode() if payload else None
    req = urllib.request.Request(f"{base_url}{endpoint}", data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.code, "body": e.read().decode()})
    except (TimeoutError, OSError, urllib.error.URLError) as e:
        return json.dumps({"error": "network", "detail": str(e)})


class VetClinicToolEnv(vf.StatefulToolEnv):
    """One container per rollout; call_api is the agent's only tool."""

    def __init__(self, max_turns: int = 40, **kwargs):
        super().__init__(tools=[], max_turns=max_turns, **kwargs)
        self.add_tool(call_api, args_to_skip=["base_url", "token_verifier", "token_app_admin"])

    def update_tool_args(self, tool_name, tool_args, messages, state, **kwargs):
        tool_args["base_url"] = state["base_url"]
        tool_args["token_verifier"] = state.get("token_verifier", "")
        tool_args["token_app_admin"] = state.get("token_app_admin", "")
        return tool_args

    async def setup_state(self, state):
        info = state.get("info") or {}
        task_id = info["task_id"]
        with open(os.path.join(TASKS_DIR, task_id, "task.json"), encoding="utf-8") as f:
            task = json.load(f)
        container = _Container()
        container.start()
        container.inject_nonce(task)
        state["_container"] = container
        state["task_id"] = task_id
        state["base_url"] = f"http://127.0.0.1:{container.host_baas_port}"
        state["token_verifier"] = container.login("verifier") or ""
        state["token_app_admin"] = container.login("app_admin") or ""
        return state


async def grade(state, **kwargs) -> float:
    """Shell out to the task's verifier.py, exactly like env.py's _compute_reward."""
    container: _Container = state["_container"]
    task_id: str = state["task_id"]
    verifier_path = os.path.join(TASKS_DIR, task_id, "verifier.py")
    try:
        result = subprocess.run(
            [sys.executable, verifier_path],
            env=dict(os.environ, VIBEDB_URL=state["base_url"]),
            capture_output=True, text=True, timeout=VERIFIER_TIMEOUT_S,
        )
        reward = 1.0 if result.returncode == 0 else 0.0
    except Exception:
        reward = 0.0
    finally:
        container.stop()
    return reward


def load_environment(task_ids: Optional[list[str]] = None, max_turns: int = 40, **kwargs) -> vf.Environment:
    """Load the veterinary_clinic_system environment (open tasks only).

    task_ids: subset of the 10 open task ids to include; defaults to all of them.
    """
    open_ids = _load_open_task_ids()
    if task_ids is not None:
        unknown = set(task_ids) - set(open_ids)
        if unknown:
            raise ValueError(f"Not open/gradable in this sample: {sorted(unknown)}")
        open_ids = [t for t in open_ids if t in task_ids]
    dataset = _build_dataset(open_ids)
    rubric = vf.Rubric(funcs=[grade])
    return VetClinicToolEnv(max_turns=max_turns, dataset=dataset, rubric=rubric, **kwargs)
