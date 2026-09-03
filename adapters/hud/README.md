# HUD adapter

Wraps the reference `../../env.py` (Gymnasium harness) as a HUD `Environment`,
following the real structure `hud init` writes (verified against the `hud`
PyPI package's own source, v0.6.15 — see `hud/cli/templates.py` in that
package — not guessed from doc summaries).

## Verified

- `env.py` and `tasks.py` **import cleanly and register all 10 open task
  templates** on the real target platform (Linux, Python 3.11, `hud`+`gymnasium`
  installed via pip) — run inside a throwaway `python:3.11-slim` container:
  `python -c "import env; print(sorted(env.env.templates.keys()))"` →
  the 10 open task ids, and `python -c "import tasks; print(len(tasks.tasks))"` → `10`.
- Fixed a real bug found this way: both this adapter and the reference harness
  are named `env.py`, which caused a circular import (`from env import
  VibeDBEnv` resolved to itself). Fixed by loading the reference file via
  `importlib.util.spec_from_file_location` under a distinct module name.
- The `Capability.mcp(...)` and `env.template`/`env.initialize`/`env.shutdown`
  signatures used here match the installed package's actual source
  (`hud/capabilities/base.py`, `hud/environment/env.py`).

## NOT verified (could not run on this machine)

- **The `hud` CLI itself cannot run on Windows.** `pip install hud` (0.6.15)
  imports fine on Linux, but on Windows/Python 3.12 it raises
  `AttributeError: module 'socketserver' has no attribute
  'ThreadingUnixStreamServer'` at import time — a Unix-only stdlib API `hud`
  imports unconditionally in `hud/environment/egress.py`. This blocked running
  `hud init`, `hud eval tasks.py claude`, or `hud serve` directly; the
  scaffold above was instead grounded by reading the installed package's
  source and confirmed with plain `python -c "import ..."` checks inside a
  Linux container (see above), which is a real but partial substitute — it
  proves the modules load and templates register, not that a full
  `hud eval`/`hud serve` round-trip against a live agent works.
- **The nested Docker launch was never actually run.** `env.py`'s templates
  call `VibeDBEnv.reset()`, which shells out to `docker run` to start
  `rl-env/veterinary_clinic_system:latest` as a *sibling* container. That
  requires the HUD environment container to have Docker CLI access (a
  mounted `/var/run/docker.sock`, per the comment in `Dockerfile.hud`) — this
  was not exercised end-to-end here (would need HUD's actual container
  runtime, or `docker run --privileged`/socket-mounted local testing, neither
  attempted in this pass).
- `hud eval`/`hud deploy`/`hud sync` were not run — they need `HUD_API_KEY`,
  which only the account owner has.

## Next steps for a human with a Linux box + HUD account

```bash
cd adapters/hud
hud set HUD_API_KEY=...
# Local test (spins up ONE container via docker; needs the vet-clinic image
# built/pulled and reachable, and the docker socket mounted if run inside a
# container itself):
uv run python env.py
# or, once the API key is set:
hud eval tasks.py claude
# Publish once the local test passes:
hud deploy
hud sync tasks my-tasks
```

Only the 10 open tasks are wired up (see repo root README.md for why the
other 90 are gated). Extending this adapter to more tasks once you have
licensed access is mechanical: add the task_id to `OPEN_TASK_IDS` in `env.py`
and import + list it in `tasks.py`.
