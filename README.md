# Long-Horizon Medical Agent Benchmark — Veterinary Clinic Ops (Sample #1)

> ### 📌 Read this first
>
> **Published by [Praesidium Compliance Systems Corporation](https://praesidiumsystems.ai)**
> · Built on **[Stackhouse](https://github.com/ArjavDesa912/stackhouse)** ([stackhousedb.com](https://stackhousedb.com))
> · [This gym on GitHub](https://github.com/ArjavDesa912/Long-Horizon-Medical-Agent-Benchmark-Veterinary-Clinic-Ops)
> · [Live on Prime Intellect](https://app.primeintellect.ai/dashboard/environments/praesidiumsystems/long-horizon-medical-agent-benchmark-vet-clinic-ops)
>
> **No LLM-as-judge, anywhere.** Every verifier is plain, deterministic Python —
> exact-value assertions, cents-normalized money comparisons, canary SHA-256
> hashing, row-level diffing against a host-side seed snapshot. No model ever
> scores the agent's work, so there's nothing for a policy to talk its way past.
> Grading is 100% on final database state.
>
> This repo is the **first sample** from a catalog of **100+ RL environments —
> each with its own 500+-task suite — already in our build pipeline, shipping
> over the coming weeks, engineered to the same reward-hacking-resistant
> standard proven below.** Every task in this sample clears a full
> reward-hacking QC battery before it ships — no-op fails, random-action
> fails, hardcoded-guess fails, gold passes, twice, deterministically — and
> that is the bar every environment coming out of the pipeline is held to, not
> just this one.
>
> **Contact us:** `arjav.desai@praesidiumsystems.ai` · `sam.heidler@praesidiumsystems.ai`

This is the first public sample from that catalog: a veterinary clinic
management system doubling as a long-horizon medical/clinical-ops agent
benchmark, engineered to the reward-hacking-resistant standard documented
below — proof of the bar the other 99+ environments now in the pipeline will
be held to as they ship.

> Full-suite access (all 98 gold solutions + verifiers + seed snapshots for
> this environment, or a custom-built 500+ task environment for your domain)
> is available under commercial license. Contact us at
> `arjav.desai@praesidiumsystems.ai` or `sam.heidler@praesidiumsystems.ai`.

## v2: same environment, a harder suite

v1 shipped 100 tasks at a 20 easy / 48 medium / 32 hard mix; frontier models
cleared all of them. v2 is a from-scratch rewrite of the task suite against
the same app and platform, aimed at closing that ceiling and every
reward-hacking angle we found in the process:

- **Every one of the 98 tasks is now hard difficulty.** Three related v1
  tasks (overdue-vaccine letters, compliance reporting, inventory coverage)
  were fused into one composite reconciliation mission instead of shipping as
  three separate easy ones — bigger, multi-hop tasks in place of a long tail
  of small ones, which is why the count moved from 100 to 98, not up.
- **Seed data grew ~7.5x** (3,071 rows across 24 collections, up from 407) and
  the episode date now jitters ±3 days per reset instead of staying fixed, so
  a memorized answer from one episode is wrong on the next.
- **Dual-path verification is now the norm, not a one-off.** v1 had exactly
  one task (`075_sql_vs_api_crosscheck`) whose whole point was cross-checking
  a Python computation against independent SQL. In v2, every verifier that
  asserts an aggregate computes it two independent ways — a raw-row Python
  filter and a separate SQL `GROUP BY`/`SUM` — and requires both to agree
  before either is compared to the agent's report, closing off "the verifier
  is keyed to one buggy computation path."
- **Every task now ships a second, independently authored reference
  solution** (`gold.py` + `gold_alt.py`), so a verifier that happens to fit
  one solution's incidental behavior (row iteration order, tie-breaking) gets
  caught by the other. Verified end-to-end for the 10 tasks open in this
  sample (`gold_alt_pass: true` in every `qc_results/<id>.json`); the gated 88
  are being run through the same check next.
- **Four real platform bugs came out of this pass**, not just task-content
  bugs — two `sqlx` decode gaps that silently nulled bare `DATE`/`TIME`
  columns and Postgres arrays, a raw-SQL endpoint that masked a real Postgres
  error as a generic 503, and a schema-evolution rate limiter that rejected a
  legitimate wide report write. All four root-caused against a live
  container and fixed; see `BUILD_NOTES.md`.

**Result: 98/98 tasks pass the full QC battery** on the rebuilt platform —
no-op fails, random-action fails, hardcoded-guess fails, the reference
solution passes, and the verifier is idempotent (see `QC_REPORT.md`).

## What this is

A Gymnasium-compatible RL environment wrapping a real, self-contained web app
(vet-clinic React frontend + a VibeDB backend-as-a-service + Postgres 15,
pre-seeded and running in Docker), with a **98-task suite** of state-change
missions: multi-step, stateful, API-driven work a compliance officer, biller,
or front-desk operator at a real clinic would actually be paid to do —
not "insert a row with field foo=bar" toy tasks.

The agent acts by issuing structured REST calls (`GET`/`POST`) against the
app's live API — no source code is written, no GUI is driven by pixels. See
[Where this fits](#where-this-fits-in-the-catalog) below for how that
distinguishes it from the code and computer-use categories we're building next.

## Why this is hard to cheat

Every task in this suite is a **state-change mission** graded on the final
database state, not on which endpoints were called. The design defends against
the standard ways a policy tries to claim reward without doing the work:

| Attack | Defense |
|---|---|
| No-op / random actions | Baselines score 0 — proven by executable test, not assumed |
| Hard-coded / memorized answers | Per-episode random nonce + a ±3-day-jittered episode date make static answers stale on every reset |
| Delete/overwrite unrelated rows to force a pass | Canary hash check over every collection outside the task's declared blast radius |
| Duplicate/stuff rows to fake a count | Exact-count + uniqueness assertions |
| Fudge one buggy aggregate computation | Every aggregate is asserted two independent ways (Python filter + SQL `GROUP BY`) before it's ever compared to the agent's report |
| Read the verifier or task files from inside the container | Verifiers and gold solutions never ship inside the Docker image — host-side only |
| Poll the grader to infer the answer | Fail-closed grading, first-failing-assertion detail cap (no full expected-value dump) |
| Flaky/lucky pass | Verifiers are deterministic; every task's QC required two consecutive identical verifier runs |
| Cross-episode contamination | Fresh `--rm` container per episode, no volumes, free ports |
| Persuade/game a fuzzy judge | No LLM-as-judge anywhere in the grading path — every verifier is plain Python asserting exact DB state (see `tools/vlib.py`) |

**Result: 98/98 tasks pass the full QC battery** — no-op fails, random-action
fails, hardcoded-guess fails, the reference solution passes, and the verifier
is idempotent — independently executed and logged per task
(see `QC_REPORT.md`, `qc_results/`, and each task's `REDTEAM.md`).

## Task suite

Every task is **hard** difficulty and carries 2-4 category tags (e.g.
`workflow,aggregation,reconciliation`) instead of one — the composite-mission
design means most tasks now span what used to be separate categories. Surface
split: 86 backend, 8 websearch, 4 frontend. **websearch**-surface tasks
require external domain knowledge (AAHA/AAFP vaccine schedules, DEA
controlled-substance recordkeeping, ISO 11784 microchip formats, AR aging
conventions); **frontend**-surface tasks replicate the exact workflow a UI
screen performs, graded on resulting state, not on driving the UI.

Every one of the 98 tasks ships its `task.json` (full mission spec) and
`REDTEAM.md` (reward-hacking threat-model notes) publicly in this repo, so
the taxonomy, difficulty calibration, and anti-cheat rigor are fully
verifiable. **10 of the 98 ship completely open** — mission, both reference
solutions, and grader — as concrete proof the other 88 are solvable the same
way:

| task | category | surface |
|---|---|---|
| `001_overdue_vaccine_compliance_flag` | update, aggregation, reconciliation | backend |
| `002_rabies_booster_due_recompute` | update, aggregation, workflow | backend |
| `003_vaccination_reminder_batch` | workflow, aggregation, reconciliation | backend |
| `011_boarding_checkin_flow` | workflow, create, aggregation | backend |
| `022_ar_aging_report` | aggregation, reconciliation | websearch |
| `028_draft_invoice_purge` | delete, create, aggregation | backend |
| `043_double_booking_repair` | repair, workflow, aggregation | backend |
| `061_new_patient_enrollment` | create, workflow, reconciliation | websearch |
| `080_enterprise_kpi_pack` | aggregation, reconciliation, workflow | backend |
| `091_idempotent_reminder_send` | idempotency, workflow, aggregation | backend |

The remaining 88 task directories include `task.json` + `REDTEAM.md` +
`ACCESS.md` (their `gold.py`/`gold_alt.py`/`verifier.py` are gated — see that
file).

## Layout

```
env.py                 # Gymnasium wrapper: container-per-episode, nonce injection, external verifier
test_env.py             # smoke test: reset -> gold.py -> verifier PASS (via env reward path)
RECON.md                 # live inventory of the app's API surface (collections, fields, routes)
BUILD_NOTES.md           # source fixes, image build log, snapshot procedure, v2 platform-bug log
QC_REPORT.md             # aggregate QC results across all 98 tasks
deploy/prime_intellect.yaml
tools/
  glib.py                # shared gold-solution library (stdlib-only)
  vlib.py                # shared verifier library (stdlib-only, read-only, fail-closed)
  qc_task.py              # per-task QC battery (noop/random/hardcode fail, gold + gold_alt pass, idempotent)
tasks/
  <id>/task.json         # mission spec (public for all 98)
  <id>/REDTEAM.md         # reward-hacking threat model notes (public for all 98)
  <id>/gold.py            # reference solution — 10 open tasks only
  <id>/gold_alt.py        # second, independently authored reference solution — 10 open tasks only
  <id>/verifier.py        # standalone PASS/FAIL grader — 10 open tasks only
  <id>/ACCESS.md          # gated-task note — 88 tasks only
qc_results/               # per-task QC transcripts — 10 open tasks only
adapters/
  hud/                    # HUD platform adapter (env.py/tasks.py/Dockerfile.hud), 10 open tasks wired
  prime-intellect/        # Prime Intellect Environments Hub adapter (verifiers spec), 10 open tasks wired
```

## Also available on HUD and Prime Intellect

`adapters/hud/` and `adapters/prime-intellect/` wire the 10 open tasks into
each platform's native format (HUD's `Environment`/task-template SDK; Prime
Intellect's `verifiers` spec). Each adapter's own README states plainly what
was actually run and verified end-to-end versus what still needs the
platform-owner's API key/login to finish publishing (`hud deploy`, `prime env
push`) — we don't claim a step is done unless we executed it.

## Run it

The Docker image (`rl-env/veterinary_clinic_system:latest`) contains only the
seeded app + VibeDB backend — no verifier, gold solution, task.json, or
expected-value artifact is ever baked in (confirmed in `BUILD_NOTES.md`), so
it's safe to run against any of the 98 tasks, gated or open. The image itself
isn't hosted from this repo yet; contact us for a pull token or a copy.

```bash
pip install gymnasium
docker pull <registry>/rl-env/veterinary_clinic_system:latest   # ask us for access
python test_env.py 001_overdue_vaccine_compliance_flag           # smoke test on an open task
```

```python
from env import VibeDBEnv

env = VibeDBEnv(app_slug="veterinary_clinic_system", task_id="001_overdue_vaccine_compliance_flag")
obs, info = env.reset()          # boots fresh container, injects episode nonce
obs, reward, terminated, truncated, info = env.step({
    "method": "GET",
    "endpoint": "/v1/query/veterinary_clinic_system_owners?limit=5",
    "payload": None,
    "as_user": "verifier",
})
env.close()
```

Rewards are computed by shelling out to the task's standalone `verifier.py`
against the episode's own mapped BaaS port — 1.0 iff the verifier exits 0.
Pointing `task_id` at a gated task still runs (the container and nonce
injection work the same way for all 98) but returns reward 0.0 with reason
`"verifier.py missing for task"`, since grading logic for those isn't shipped
here.

## Where this fits in the catalog

This environment is a **long-horizon, tool-use agent environment**: the policy
only ever emits structured API calls against a live backend and is graded on
resulting database state — no source code is written or edited, and no GUI is
driven by pixels/screenshots. It sits in the same family as agentic
tool-use/backend-automation benchmarks, distinct from:

- **Code environments** (SWE-bench-style: the agent edits a codebase, graded
  by a test suite) — a separate category in our roadmap.
- **Computer-use environments** (OSWorld-style: the agent drives a real GUI
  via mouse/keyboard/screenshots) — also a separate category we're building.

The `websearch`-surface tasks in this suite add a knowledge-retrieval
dimension (real domain standards the agent must look up, not just compute from
seed data), previewing how we compose categories rather than treat them as
silos.

## Get the full suite, or a custom environment

We build these to order: pick a domain, we ship a Docker-packaged app +
100–500+ verified, reward-hacking-resistant tasks against it, QC'd exactly
like this one — and we have **100+ of these environments in the pipeline,
shipping over the coming weeks**, this one included. Contact **Praesidium
Compliance Systems Corporation**:

- Email — `arjav.desai@praesidiumsystems.ai` or `sam.heidler@praesidiumsystems.ai`
- Web — [praesidiumsystems.ai](https://praesidiumsystems.ai)
- This gym — [GitHub](https://github.com/ArjavDesa912/Long-Horizon-Medical-Agent-Benchmark-Veterinary-Clinic-Ops) · [Prime Intellect](https://app.primeintellect.ai/dashboard/environments/praesidiumsystems/long-horizon-medical-agent-benchmark-vet-clinic-ops)
- Stack — [Stackhouse on GitHub](https://github.com/ArjavDesa912/stackhouse) · [stackhousedb.com](https://stackhousedb.com)
