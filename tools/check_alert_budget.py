from erp.security_hardening import safe_run, safe_call, safe_popen
#!/usr/bin/env python3
import sys, subprocess

def run(cmd):
    print("+", " ".join(cmd))
    p = safe_run(cmd, capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
    return p.returncode

if run(["pip", "install", "pip-audit", "gitleaks"]) != 0:
    sys.exit(1)

rc_audit = run(["pip-audit", "-f", "json"])
rc_leaks = run(["gitleaks", "detect", "--no-banner", "--report-format", "json", "--report-path", "gitleaks.json"])

if rc_audit != 0 or rc_leaks != 0:
    print("Security alert SLO breached (vulns or secrets found)")
    sys.exit(1)

print("Alert budget OK")

