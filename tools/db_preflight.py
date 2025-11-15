import os, sys, urllib.parse
import psycopg2

url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
if not url:
    raise SystemExit("DATABASE_URL not set")

# Normalize to a psycopg2-friendly scheme and separate the 'postgres' maintenance DB
pg_url = url.replace("postgresql+psycopg2", "postgres")
u = urllib.parse.urlparse(pg_url)
db = (u.path or "/").lstrip("/") or "postgres"

# Connect to the maintenance database 'postgres' to create the target DB if missing
root_url = pg_url.replace(f"/{db}", "/postgres")

conn = psycopg2.connect(root_url)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db,))
if not cur.fetchone():
    cur.execute(f'CREATE DATABASE "{db}"')
print("DB ready:", db)
