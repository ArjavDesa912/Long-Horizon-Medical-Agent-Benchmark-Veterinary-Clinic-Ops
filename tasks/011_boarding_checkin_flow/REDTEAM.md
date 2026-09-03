# REDTEAM — 011_boarding_checkin_flow

| Attack | Defense | Result |
|---|---|---|
| No-op / random actions | Pristine state has the target reservation 'reserved' -> FAIL; random writes break byte-identity -> FAIL | covered by baselines |
| Hard-code expected values | Target reservation is an argmin over live check_in dates (shift per rebuild); verifier recomputes from live data | enforced |
| Delete/overwrite seed rows | All out-of-scope rows byte-compared to snapshot; counts exact | enforced |
| Duplicate/stuff rows | Exact counts on both collections | enforced |
| Tamper with verifier/task.json | Host-side verifier; hash check at grade time | enforced |
| Poll verifier to infer values | First-failing-assertion cap | enforced |
| Raw SQL bypass | Allowed; state assertions still apply | by design |
| Crash grader | Fail-closed | enforced |
| Flaky-pass retry | Deterministic; 2 consecutive runs in QC | enforced |
| Cross-episode contamination | Fresh --rm container per episode | enforced |
