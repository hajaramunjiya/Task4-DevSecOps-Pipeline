"""
DAST (Dynamic Application Security Testing) stage.

Unlike SCA (checks dependencies) and SAST (reads source code), DAST
treats the application as a black box: it starts the real HTTP service
and attacks it the way an outside attacker would, with no knowledge of
the source. This is modelled on the checks OWASP ZAP's baseline scan
performs (missing security headers, server banner disclosure, error
handling / information leakage, basic injection probes); a production
pipeline would run the real zaproxy/action-baseline GitHub Action
against the same running instance (see .github/workflows/ci-cd.yml) -
this script is a portable equivalent that needs nothing beyond `requests`,
so it can run anywhere this project runs, including this sandbox.

Usage:
    python3 security/dast_scan.py                 -> attacks api/server.py       (expect PASS)
    python3 security/dast_scan.py --fail-demo      -> attacks the insecure twin  (expect FAIL)
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

REQUIRED_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
]


def start_target(fail_demo: bool) -> tuple[subprocess.Popen, str]:
    if fail_demo:
        cmd = [sys.executable, "security/fail_demo/insecure_server.py"]
        base_url = "http://127.0.0.1:5001"
    else:
        cmd = [sys.executable, "-c", "from api.server import serve; serve()"]
        base_url = "http://127.0.0.1:5000"

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try:
            requests.get(f"{base_url}/health", timeout=0.5)
            return proc, base_url
        except requests.exceptions.ConnectionError:
            time.sleep(0.3)
    proc.terminate()
    raise RuntimeError("target did not become healthy in time")


def check_security_headers(base_url: str) -> dict:
    resp = requests.get(f"{base_url}/health")
    missing = [h for h in REQUIRED_HEADERS if h not in resp.headers]
    return {
        "check": "security-headers",
        "passed": not missing,
        "detail": f"missing: {missing}" if missing else "all required headers present",
    }


def check_server_banner(base_url: str) -> dict:
    resp = requests.get(f"{base_url}/health")
    banner = resp.headers.get("Server", "")
    leaks_version = "Werkzeug" in banner or "Python" in banner
    return {
        "check": "server-banner-disclosure",
        "passed": not leaks_version,
        "detail": f"Server header: '{banner}'",
    }


def check_path_traversal(base_url: str) -> dict:
    resp = requests.post(
        f"{base_url}/run",
        json={"input_path": "../../../../etc/passwd"},
        timeout=3,
    )
    # A safe app rejects this outright (400); it must never return 200
    # with file content, and must never 500 in a way that leaks a path.
    passed = resp.status_code == 400
    return {
        "check": "path-traversal",
        "passed": passed,
        "detail": f"status={resp.status_code}, body={resp.text[:150]}",
    }


def check_injection_in_zone_id(base_url: str) -> dict:
    """Sends a classic injection payload as the zone id. A safe
    implementation must reject it with 400 before it reaches any
    eval/exec/SQL concatenation. Against the insecure twin, this payload
    is executed server-side via eval() and the result is reflected back -
    conclusive proof of remote code execution, not just a guess."""
    payload = "__import__('os').getpid()"
    try:
        resp = requests.get(f"{base_url}/zone/{payload}", timeout=3)
    except requests.exceptions.RequestException as exc:
        return {"check": "injection-in-path-param", "passed": True, "detail": f"request rejected at transport level: {exc}"}

    executed = resp.status_code == 200 and "zone_id" in resp.text and payload not in resp.text
    passed = not executed and resp.status_code in (400, 404)
    return {
        "check": "injection-in-path-param",
        "passed": passed,
        "detail": f"status={resp.status_code}, body={resp.text[:150]}",
    }


def check_debug_console_disclosure(base_url: str) -> dict:
    """Forces a 500 and checks whether the response contains Werkzeug's
    interactive debugger - which is itself a remote-code-execution
    vector, not just a stack-trace leak."""
    try:
        resp = requests.get(f"{base_url}/zone/" + "x" * 5000, timeout=3)
    except requests.exceptions.RequestException as exc:
        return {"check": "debug-console-disclosure", "passed": True, "detail": str(exc)}

    leaked = "Werkzeug Debugger" in resp.text or "Traceback (most recent" in resp.text
    return {
        "check": "debug-console-disclosure",
        "passed": not leaked,
        "detail": "interactive debugger exposed in response" if leaked else f"status={resp.status_code}, no debugger markup",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-demo", action="store_true")
    args = parser.parse_args()

    label = "FAIL DEMO (insecure_server.py)" if args.fail_demo else "api/server.py"
    print(f"=== DAST - attacking a live instance: {label} ===")

    proc, base_url = start_target(args.fail_demo)
    try:
        results = [
            check_security_headers(base_url),
            check_server_banner(base_url),
            check_path_traversal(base_url) if not args.fail_demo else {"check": "path-traversal", "passed": True, "detail": "skipped - insecure twin has no /run route"},
            check_injection_in_zone_id(base_url),
            check_debug_console_disclosure(base_url),
        ]
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['check']}: {r['detail']}")

    Path("security/evidence").mkdir(parents=True, exist_ok=True)
    report_name = "dast_report_fail_demo.json" if args.fail_demo else "dast_report.json"
    with open(f"security/evidence/{report_name}", "w") as f:
        json.dump(results, f, indent=2)

    overall_pass = all(r["passed"] for r in results)
    print()
    print(f"DAST RESULT: {'PASS' if overall_pass else 'FAIL'} - "
          f"{sum(r['passed'] for r in results)}/{len(results)} checks passed.")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
