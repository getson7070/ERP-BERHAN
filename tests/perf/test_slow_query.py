import time
from sqlalchemy import create_engine, text


def test_simple_query_fast(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/perf.db")
    start = time.perf_counter()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    duration = time.perf_counter() - start
    assert duration < 0.1, f"query took {duration} seconds"


