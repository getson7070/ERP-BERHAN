#!/usr/bin/env python3
import os, sys, time, json
import requests

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
ADMIN = os.environ.get("SMOKE_ADMIN_USER", "")
PASS  = os.environ.get("SMOKE_ADMIN_PASS", "")

def fail(msg, code=1):
    print(f"[SMOKE][FAIL] {msg}", file=sys.stderr)
    sys.exit(code)

def get(path):
    r = requests.get(BASE + path, timeout=15)
    print("[GET]", path, r.status_code)
    return r

def post(path, payload):
    r = requests.post(BASE + path, json=payload, timeout=20)
    print("[POST]", path, r.status_code, payload)
    return r

if not BASE:
    fail("SMOKE_BASE_URL not set")

# 1) health
r = get("/health")
if r.status_code != 200:
    fail("Healthcheck failed")

# 2) login
tok = None
r = post("/api/auth/login", {"username": ADMIN, "password": PASS})
if r.status_code == 200:
    try:
        tok = r.json().get("token") or r.cookies.get("session")
    except Exception:
        pass
if not tok:
    fail("Login failed")

# 3) finance write (idempotent test)
headers = {"Authorization": f"Bearer {tok}"} if tok and " " not in tok else {}
r = requests.post(BASE + "/api/finance/txns", json={"amount": 0, "memo": "smoke"}, headers=headers, timeout=20)
if r.status_code not in (200, 201, 409):
    fail(f"Finance write failed: {r.status_code}")

# 4) analytics read
r = requests.get(BASE + "/api/analytics/ping", headers=headers, timeout=15)
if r.status_code != 200:
    fail("Analytics read failed")

print("[SMOKE] OK")
