#!/usr/bin/env bash
# SAST (Static Application Security Testing) stage.
#
# Reads the application's own source code (without running it) looking
# for known-dangerous patterns: eval/exec, shell=True, hardcoded secrets,
# insecure deserialisation, weak hashing, etc. This is the stage that
# catches a flaw WE wrote, as opposed to SCA (a flaw in a dependency) or
# DAST (a flaw only visible when the app is actually running).
#
# Usage:
#   ./security/run_sast.sh             -> scans src/ and api/ (expect PASS)
#   ./security/run_sast.sh --fail-demo -> scans security/fail_demo/ as well
#                                         (expect FAIL - eval(), hardcoded
#                                         secret key)
set -uo pipefail

if [[ "${1:-}" == "--fail-demo" ]]; then
    TARGETS="src api security/fail_demo"
    echo "=== SAST (bandit) - FAIL DEMO: scanning src/, api/, AND security/fail_demo/ ==="
else
    TARGETS="src api"
    echo "=== SAST (bandit) - scanning $TARGETS ==="
fi

bandit -r $TARGETS -ll -f txt
STATUS=$?

echo
if [[ $STATUS -eq 0 ]]; then
    echo "SAST RESULT: PASS - no medium/high severity findings in scanned source."
else
    echo "SAST RESULT: FAIL - bandit found a medium/high severity issue."
    echo "A CI/CD pipeline stops here: the build stage never runs."
fi
exit $STATUS
