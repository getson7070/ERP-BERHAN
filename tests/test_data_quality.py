import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime, UTC, timedelta
from erp.data_quality import deduplicate, detect_conflict
from db import get_db
import pytest


def test_deduplicate():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS tmp (org_id INT, name TEXT)")
    cur.execute("INSERT INTO tmp (org_id, name) VALUES (1,'A'),(1,'A'),(1,'B')")
    conn.commit()
    removed = deduplicate("tmp", ["org_id", "name"])
    assert removed == 1
    cur.execute("DROP TABLE tmp")
    conn.commit()
    cur.close()
    conn.close()


def test_deduplicate_rejects_invalid_identifier():
    with pytest.raises(ValueError):
        deduplicate("tmp;DROP TABLE users;", ["name"])
    with pytest.raises(ValueError):
        deduplicate("tmp", ["name;DROP TABLE users;"])


def test_detect_conflict():
    now = datetime.now(UTC)
    assert detect_conflict(now, now - timedelta(seconds=10)) is True
    assert detect_conflict(now, now + timedelta(seconds=10)) is False
