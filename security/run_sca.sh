#!/usr/bin/env bash
# SCA (Software Composition Analysis) stage.
#
# Checks every third-party package the application actually depends on
# against the OSV (Open Source Vulnerabilities) advisory database via
# pip-audit. This is the stage that catches a vulnerable DEPENDENCY -
# code we didn't write but ship anyway - which neither SAST (which only
# reads code we wrote) nor unit tests (which only check our own logic)
# will ever find.
#
# Usage:
#   ./security/run_sca.sh            -> audits the real requirements.txt (expect PASS)
#   ./security/run_sca.sh --fail-demo -> audits a deliberately vulnerable
#                                        requirements file (expect FAIL)
set -uo pipefail

if [[ "${1:-}" == "--fail-demo" ]]; then
    TARGET="security/requirements-vulnerable-demo.txt"
    echo "=== SCA (pip-audit) - FAIL DEMO: scanning a deliberately vulnerable dependency pin ==="
else
    TARGET="requirements.txt"
    echo "=== SCA (pip-audit) - scanning $TARGET ==="
fi

pip-audit -r "$TARGET"
STATUS=$?

echo
if [[ $STATUS -eq 0 ]]; then
    echo "SCA RESULT: PASS - no known vulnerabilities in any pinned dependency."
else
    echo "SCA RESULT: FAIL - one or more dependencies have a published CVE/advisory."
    echo "A CI/CD pipeline stops here: the build stage never runs."
fi
exit $STATUS
