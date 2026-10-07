# Automated Test Specification - Task 4

**System under test:** the Task 3 NYC Taxi Demand Analytics application, accessed
both as a library (`src/`) and as a live HTTP service (`api/server.py`).

## Scope

| # | Stage | Tool | What it checks | Gate |
|---|-------|------|-----------------|------|
| 1 | SCA | pip-audit (vs. the OSV advisory database) | Every pinned third-party dependency in `requirements.txt` for published CVEs/advisories | Fails the build if any dependency has a known vulnerability |
| 2 | SAST | bandit | Our own Python source (`src/`, `api/`) for dangerous patterns: `eval`/`exec`, `debug=True`, shell injection, insecure deserialisation, hardcoded secrets, weak hashing | Fails the build on any medium/high severity finding |
| 3 | Unit & integration tests | pytest | Functional correctness: data validation, feature transforms, demand aggregation, Liskov-substitutability of swappable components, and the HTTP API's request handling | Fails the build on any failing assertion |
| 4 | Build | Python import check | The package actually imports/instantiates cleanly | Fails the build if imports error |
| 5 | DAST | custom black-box scanner (`security/dast_scan.py`), modelled on OWASP ZAP baseline checks; OWASP ZAP baseline itself in the GitHub Actions workflow | The *running* service: security headers, server banner disclosure, path traversal, injection in path parameters, debug-console disclosure | Fails the build on any failed dynamic check |

## Pass criteria
All five stages must exit 0. Stages run in the order above and each stage only
runs if the previous one passed (`needs:` in the GitHub Actions workflow;
`run_stage`'s early exit in the local script) - cheapest, fastest checks first.

## Fail-demo mode
Every stage has a `--fail-demo` mode that substitutes a deliberately flawed
artefact (a vulnerable dependency pin for SCA, an insecure Flask app for SAST/DAST)
so the specification can be *proven* to catch real issues, not just assumed to.

## How to run

```bash
./security/run_pipeline.sh              # full pipeline against the real app   -> PASS
./security/run_pipeline.sh --fail-demo  # full pipeline, deliberately flawed   -> FAIL (stops at SCA)

./security/run_sca.sh / --fail-demo
./security/run_sast.sh / --fail-demo
python3 security/dast_scan.py / --fail-demo
python3 -m pytest tests/ -v
```

Console output from an actual run of each is saved under `security/evidence/`.
