#!/usr/bin/env python3
import sys, json, subprocess

# Example: run pip-audit & gitleaks and fail if high severity found
def run(cmd):
    print("+", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(p.stdout)
    print(p.stderr, file=sys.stderr)
    return p.returncode, p.stdout

rc, _ = run(["pip", "install", "pip-audit", "gitleaks"])
rc_audit, _ = run(["pip-audit", "-f", "json"])
rc_leaks = subprocess.run(["gitleaks", "detect", "--no-banner", "--report-format", "json", "--report-path", "gitleaks.json"]).returncode

# If either tool fails, fail this job
if rc_audit != 0 or rc_leaks != 0:
    sys.exit(1)

print("Alert budget: OK")
