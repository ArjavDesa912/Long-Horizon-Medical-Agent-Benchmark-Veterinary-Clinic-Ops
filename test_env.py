#!/usr/bin/env python3
"""
Smoke test for the veterinary_clinic_system RL environment.

Per RL_ENV_FACTORY_PROMPT Phase 5: reset -> gold.py for a task -> verifier PASS,
exercised end-to-end through the Gymnasium wrapper (reward comes from the
env shelling out to the task's host-side verifier).

Usage:
    python test_env.py [task_id]     (default: 021_overdue_invoice_flagging)
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import VibeDBEnv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    task_id = sys.argv[1] if len(sys.argv) > 1 else "021_overdue_invoice_flagging"
    task_dir = os.path.join(HERE, "tasks", task_id)
    assert os.path.isdir(task_dir), f"unknown task {task_id}"

    env = VibeDBEnv(app_slug="veterinary_clinic_system", task_id=task_id)
    try:
        print(f"Resetting environment (task={task_id})...")
        observation, info = env.reset()
        print(f"nonce: {info.get('nonce')}")
        print(f"observation tables: {len(__import__('json').loads(observation)['tables'])}")

        print("\nBaseline step (GET /health) — reward must be 0.0 on pristine state:")
        obs, reward, terminated, truncated, info = env.step({
            "method": "GET", "endpoint": "/health", "payload": None, "as_user": "verifier",
        })
        print(f"  reward={reward} reason={info.get('reward_reason')}")
        assert reward == 0.0, "no-op baseline must score 0"

        print(f"\nRunning gold.py for {task_id} against the live container...")
        result = subprocess.run(
            [sys.executable, os.path.join(task_dir, "gold.py")],
            env=dict(os.environ, VIBEDB_URL=f"http://127.0.0.1:{env.host_baas_port}"),
            capture_output=True, text=True, timeout=300,
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            raise AssertionError("gold.py failed")

        print("\nGrading via env.step (GET /health triggers the external verifier)...")
        obs, reward, terminated, truncated, info = env.step({
            "method": "GET", "endpoint": "/health", "payload": None, "as_user": "verifier",
        })
        print(f"  reward={reward} terminated={terminated} reason={info.get('reward_reason')}")
        assert reward == 1.0 and terminated, "verifier must PASS after gold"

        print("\nSmoke test passed.")
    finally:
        print("Closing environment (stopping container)...")
        env.close()


if __name__ == "__main__":
    main()
