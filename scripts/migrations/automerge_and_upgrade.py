import os
import subprocess
import shlex


def normalize_database_url(url: str) -> str:
    # Render commonly supplies postgres://... ; SQLAlchemy wants postgresql+psycopg2://...
    if url and url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    return url


def run(cmd: str) -> None:
    print(f"$ {cmd}")
    subprocess.check_call(shlex.split(cmd))


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")

    os.environ["DATABASE_URL"] = normalize_database_url(url)

    # Safe even if already stamped
    try:
        run("alembic -c alembic.ini stamp 8de54ef00dfe")
    except subprocess.CalledProcessError as e:
        print(f"stamp ignored: {e}")

    # Upgrade to single head (0001_initial_core)
    run("alembic -c alembic.ini upgrade head")


if __name__ == "__main__":
    main()
