import os, subprocess, shlex

def normalize_database_url(url: str) -> str:
    return "postgresql+psycopg2://" + url[len("postgres://"):] if url and url.startswith("postgres://") else url

def run(cmd: str) -> None:
    print(f"$ {cmd}")
    subprocess.check_call(shlex.split(cmd))

if __name__ == "__main__":
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    os.environ["DATABASE_URL"] = normalize_database_url(url)
    try:
        run("alembic -c alembic.ini stamp 8de54ef00dfe")
    except subprocess.CalledProcessError:
        pass
    run("alembic -c alembic.ini upgrade head")

