"""Run Alembic migrations and verify schema before and after."""

import os
import subprocess
import time
from typing import List

from sqlalchemy import create_engine, inspect


EXPECTED_TABLES: List[str] = ["users", "roles"]


def main() -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    start = time.time()
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    engine = create_engine(db_url)
    insp = inspect(engine)
    missing = [t for t in EXPECTED_TABLES if not insp.has_table(t)]
    if missing:
        print(f"migration_verify_up_success=0 missing_tables={','.join(missing)}")
    else:
        print("migration_verify_up_success=1")

    subprocess.run(["alembic", "downgrade", "base"], check=True)
    insp = inspect(engine)
    residual = [t for t in EXPECTED_TABLES if insp.has_table(t)]
    if residual:
        print(f"migration_verify_down_success=0 residual_tables={','.join(residual)}")
    else:
        print("migration_verify_down_success=1")

    engine.dispose()

    duration = time.time() - start
    print(f"migration_duration_seconds={duration:.2f}")


if __name__ == "__main__":
    main()
