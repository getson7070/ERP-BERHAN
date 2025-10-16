import os
import subprocess
import sys

def normalize(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url

def main() -> int:
    db = normalize(os.environ.get("DATABASE_URL", ""))
    if not db:
        print("DATABASE_URL is not set; cannot run migrations.", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["DATABASE_URL"] = db

    # Try to stamp the baseline (no-op if table already exists / version is set)
    subprocess.run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "stamp", "8de54ef00dfe"], check=False, env=env)
    # Upgrade to head
    subprocess.run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"], check=True, env=env)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
