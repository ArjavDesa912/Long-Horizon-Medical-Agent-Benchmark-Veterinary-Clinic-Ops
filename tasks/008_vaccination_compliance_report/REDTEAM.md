# REDTEAM — 008_vaccination_compliance_report

| Attack | Defense | Result |
|---|---|---|
| No-op / random actions | No report rows in pristine seed -> FAIL; random rows miss exact-count/per-type assertions -> FAIL | covered by baselines |
| Hard-code expected values | batch_code is a fresh per-episode nonce; totals/overdue derive from live vaccinations vs the per-episode episode_date | verifier recomputes live |
| Delete/overwrite seed rows | vaccinations canary hash must match snapshot; ops_reports has exact row count | enforced |
| Duplicate/stuff rows | Exact count (5) + per-type map uniqueness | enforced |
| Tamper with verifier/task.json | Host-side verifier; env re-hashes task files at grade time | enforced |
| Poll verifier to infer values | First-failing-assertion cap; read-only traffic | enforced |
| Raw SQL bypass | Allowed; all state assertions still apply | by design |
| Crash grader | Fail-closed | enforced |
| Flaky-pass retry | Deterministic; 2 consecutive runs in QC | enforced |
| Cross-episode contamination | Fresh --rm container per episode | enforced |
