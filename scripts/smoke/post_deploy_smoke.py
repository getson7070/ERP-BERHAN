import os, sys, time, requests

BASE_URL = os.environ.get("SMOKE_BASE_URL")
LOGIN_PATH = os.environ.get("SMOKE_LOGIN_PATH", "/auth/login")
PING_PATH = os.environ.get("SMOKE_PING_PATH", "/api/ping")
HEALTH_PATH = os.environ.get("SMOKE_HEALTH_PATH", "/healthz")

REQUIRED = ["SMOKE_BASE_URL"]
missing = [k for k in REQUIRED if not os.environ.get(k)]
if missing:
    print(f"Skipping smoke: missing {missing}. Set these env vars in CI to enable.")
    sys.exit(0)  # skip, not fail

def get(path):
    url = BASE_URL.rstrip("/") + path
    r = requests.get(url, timeout=10)
    print(path, r.status_code)
    r.raise_for_status()
    return r

def main():
    start = time.time()
    get(HEALTH_PATH)
    get(PING_PATH)
    get(LOGIN_PATH)
    elapsed = time.time() - start
    print(f"Smoke OK in {elapsed:.2f}s")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("SMOKE FAILED:", e)
        sys.exit(1)
