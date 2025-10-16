import os
import subprocess
import shlex


def normalize_database_url(url: str) -> str:
    # Render may supply postgres://... ; SQLAlchemy wants postgresql+psycopg2://...
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

    # Idempotent if already stamped
    try:
        run("alembic -c alembic.ini stamp 8de54ef00dfe")
    except subprocess.CalledProcessError as e:
        print(f"stamp ignored: {e}")

    run("alembic -c alembic.ini upgrade head")


if __name__ == "__main__":
    main()