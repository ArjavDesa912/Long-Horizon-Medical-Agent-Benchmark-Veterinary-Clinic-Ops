# veterinary-clinic-system

### Overview
- **Environment ID**: `veterinary-clinic-system`
- **Short description**: Long-horizon, tool-use agent missions against a live vet-clinic REST backend (VibeDB) — state-change tasks graded on final database state via a standalone host-side verifier, not string matching.
- **Tags**: agentic, tool-use, long-horizon, backend-automation, reward-hacking-resistant

### Datasets
- **Primary dataset(s)**: Built live at load time from `tasks/<id>/task.json` — one row per open task, `question` = the task's natural-language mission instruction, `info` = `{"task_id": ...}`.
- **Source links**: Published by Praesidium Compliance Systems Corporation — https://praesidiumsystems.ai. Full 100-task suite (this sample ships 10 open + 90 gated) available under commercial license: arjav.desai@praesidiumsystems.ai.
- **Split sizes**: 10 open tasks (no held-out eval split in this public sample; the other 90 are gated, not a split).

### Task
- **Type**: multi-turn tool use
- **Output format expectations**: none — the agent only calls the `call_api` tool (`method`, `endpoint`, `payload`, `as_user`); there is no final text answer to parse.
- **Rubric overview**: one reward function, `grade`, which shells out to the task's own `verifier.py` against the episode's live container and returns `1.0` iff it exits 0, else `0.0`. No inline scoring logic that can drift from the standalone verifier.

### Quickstart
Requires Docker (the environment launches `rl-env/veterinary_clinic_system:latest` per rollout) and `VETCLINIC_REPO_ROOT` set if this package isn't installed inside the sample repo checkout (see adapters/prime-intellect/README.md).

```bash
prime eval run veterinary-clinic-system
```

Configure model and sampling:

```bash
prime eval run veterinary-clinic-system -m openai/gpt-4.1-mini -n 10 -r 1 -t 4096 -T 0.7
```

### Taskset Config

| Field | Type | Default | Description |
| --- | ---- | ------- | ----------- |
| `task_ids` | list[str] \| None | all 10 open tasks | Restrict to a subset of open task ids |
| `max_turns` | int | `40` | Tool-call turn budget per episode, matching this task suite's `max_steps` |

### Harness Config
None beyond the standard `verifiers` eval harness — no custom sampling/harness fields.

### Metrics

| Metric | Meaning |
| ------ | ------- |
| `reward` | `1.0` iff the task's verifier.py exits 0 against the episode's final database state, else `0.0` |
