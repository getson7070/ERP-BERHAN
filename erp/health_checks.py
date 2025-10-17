import os, time, socket
from typing import Dict, Any

def version_info():
    return {
        "service": os.getenv("SERVICE_NAME", "erp-berhan"),
        "env": os.getenv("FLASK_ENV", "production"),
        "git_sha": os.getenv("GIT_SHA", "unknown"),
    }

def _ok(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, **payload}

def _fail(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": False, **payload}

def check_database(timeout: float = 1.5) -> Dict[str, Any]:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return _fail({"error": "DATABASE_URL not set"})
    try:
        # Lazy import to avoid hard dependency if you don't enable readyz
        import psycopg2
        import psycopg2.extras  # noqa: F401
        import urllib.parse as up
        # Normalize for psycopg2 if a SQLAlchemy URL is used
        # Accept both postgresql and postgresql+psycopg2
        pg_url = url.replace("+psycopg2", "")
        conn = psycopg2.connect(pg_url, connect_timeout=int(timeout))
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return _ok({"url": _redact(url)})
    except Exception as e:
        return _fail({"url": _redact(url), "error": str(e)})

def check_redis(timeout: float = 1.0) -> Dict[str, Any]:
    url = os.getenv("REDIS_URL", "")
    if not url:
        return _fail({"error": "REDIS_URL not set"})
    try:
        import redis
        r = redis.StrictRedis.from_url(url, socket_timeout=timeout)
        r.ping()
        return _ok({"url": _redact(url)})
    except Exception as e:
        return _fail({"url": _redact(url), "error": str(e)})

def _redact(url: str) -> str:
    # Hide credentials in URLs for logs and JSON output
    if "@" in url and "://" in url:
        prefix, rest = url.split("://", 1)
        if "@" in rest:
            creds, host = rest.split("@", 1)
            return f"{prefix}://****:****@{host}"
    return url
