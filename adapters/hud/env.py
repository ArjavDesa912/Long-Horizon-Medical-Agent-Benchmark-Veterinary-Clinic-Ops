"""veterinary-clinic-system — HUD environment adapter.

Wraps the reference ``VibeDBEnv`` (../../env.py, the Gymnasium harness this
repo ships) instead of reimplementing container lifecycle / VibeDB HTTP /
nonce injection: this file only translates that harness into HUD's
Environment/template/capability model.

Structure verified against the real ``hud`` package (v0.6.15) source at
``hud/cli/templates.py`` (what ``hud init`` actually writes) — the ``hud``
CLI itself could not be *run* on this machine (Windows + Python 3.12; the
installed package raises ``AttributeError: module 'socketserver' has no
attribute 'ThreadingUnixStreamServer'`` on import, a Unix-only API HUD 0.6.15
imports unconditionally). See adapters/hud/README.md for exactly what that
means for you.

Only the 10 "open" tasks (task.json + gold.py + verifier.py all present) are
wired up here — the other 90 ship task.json/REDTEAM.md only in this sample,
so there is no verifier to grade against.
"""

import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path

ADAPTER_DIR = Path(__file__).resolve().parent
REPO_ROOT = ADAPTER_DIR.parent.parent

# Both this file and the reference harness are named env.py, so a plain
# `sys.path.insert` + `import env` resolves to *this* (partially-initialized)
# module instead — load the reference module under a distinct name instead.
_spec = importlib.util.spec_from_file_location("_reference_env", REPO_ROOT / "env.py")
_reference_env = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reference_env)
VibeDBEnv = _reference_env.VibeDBEnv

from hud.capabilities import Capability
from hud.environment import Environment
from fastmcp import FastMCP

OPEN_TASK_IDS = [
    "001_overdue_vaccine_compliance_flag",
    "002_rabies_booster_due_recompute",
    "003_vaccination_reminder_batch",
    "011_boarding_checkin_flow",
    "022_ar_aging_report",
    "028_draft_invoice_purge",
    "043_double_booking_repair",
    "061_new_patient_enrollment",
    "080_enterprise_kpi_pack",
    "091_idempotent_reminder_send",
]

MCP_PORT = 8766

env = Environment(name="veterinary-clinic-system")
mcp = FastMCP(name="veterinary-clinic-system-tools")

# One VibeDBEnv (one live container) per running episode. HUD spins up a
# fresh copy of this whole environment (per Dockerfile.hud) per task run, so
# a single module-level slot is correct here — see README.md "Concurrency".
_active: dict[str, VibeDBEnv | None] = {"env": None}


@mcp.tool()
async def api_call(method: str, endpoint: str, payload: str | None = None, as_user: str = "verifier") -> str:
    """Issue one REST call against the running VibeDB backend.

    Mirrors the action shape of the reference Gymnasium env's action_space:
    {method, endpoint, payload (JSON string or null), as_user}.
    """
    ve = _active["env"]
    if ve is None:
        return json.dumps({"error": "no active episode container"})
    body = json.loads(payload) if payload else None
    token = ve._login(as_user)

    def _do():
        return ve._http(method, endpoint, body, token=token)

    status, resp = await asyncio.to_thread(_do)
    return json.dumps({"status": status, "body": resp})


def _make_task(task_id: str):
    task_json_path = REPO_ROOT / "tasks" / task_id / "task.json"
    verifier_path = REPO_ROOT / "tasks" / task_id / "verifier.py"

    @env.template(id=task_id)
    async def _template():
        instruction = json.loads(task_json_path.read_text())["instruction"]

        ve = VibeDBEnv(app_slug="veterinary_clinic_system", task_id=task_id)
        await asyncio.to_thread(ve.reset)
        _active["env"] = ve
        try:
            asyncio.create_task(mcp.run_http_async(host="127.0.0.1", port=MCP_PORT))
            await asyncio.sleep(0.2)
            env.add_capability(Capability.mcp(name="tools", url=f"http://127.0.0.1:{MCP_PORT}/mcp"))

            # First yield: the prompt. Resumes (via asend) once the agent
            # signals it's done acting; the returned "answer" text is unused —
            # grading is state-based, via the standalone verifier below.
            yield instruction

            def _grade():
                import subprocess

                proc = subprocess.run(
                    [sys.executable, str(verifier_path)],
                    env={**os.environ, "VIBEDB_URL": f"http://127.0.0.1:{ve.host_baas_port}"},
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                return proc.returncode == 0

            passed = await asyncio.to_thread(_grade)
            yield 1.0 if passed else 0.0
        finally:
            await asyncio.to_thread(ve.close)
            _active["env"] = None

    return _template


for _task_id in OPEN_TASK_IDS:
    globals()[_task_id.split("_", 1)[1]] = _make_task(_task_id)


# ============================================================================
# TEST — run with: uv run python env.py   (spins up ONE container via docker;
# needs the rl-env/veterinary_clinic_system:latest image and Docker socket
# access — see README.md)
# ============================================================================

async def test():
    from hud import LocalRuntime
    from hud.agents.claude import ClaudeAgent

    agent = ClaudeAgent()
    task = globals()["overdue_vaccine_compliance_flag"]()
    job = await task.run(agent, runtime=LocalRuntime(__file__))
    print("reward:", job.reward)


if __name__ == "__main__":
    asyncio.run(test())
