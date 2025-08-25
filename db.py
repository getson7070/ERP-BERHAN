import os
import sqlite3
from queue import Queue, Empty

DATABASE_PATH = os.environ.get('DATABASE_PATH', 'erp.db')

_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '5'))
_pool: Queue[sqlite3.Connection] = Queue(maxsize=_POOL_SIZE)
_pool_path = DATABASE_PATH

class PooledConnection:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def __getattr__(self, attr):
        return getattr(self._conn, attr)

    def close(self):
        _pool.put(self._conn)


def _create_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def get_db():
    global _pool_path
    if _pool_path != DATABASE_PATH:
        while not _pool.empty():
            _pool.get_nowait().close()
        _pool_path = DATABASE_PATH
    try:
        conn = _pool.get_nowait()
    except Empty:
        conn = _create_conn()
    return PooledConnection(conn)
