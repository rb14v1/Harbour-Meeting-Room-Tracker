import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import DB_PATH


def get_connection(db_path=DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


@contextmanager
def read_connection(db_path=DB_PATH) -> Iterator[sqlite3.Connection]:
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def write_transaction(db_path=DB_PATH) -> Iterator[sqlite3.Connection]:
    """Open a write transaction that takes the SQLite write lock up front (BEGIN IMMEDIATE).

    Concurrent booking attempts are serialised at the database level, so the overlap
    check and the insert happen atomically.
    """
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def init_database(db_path=DB_PATH) -> None:
    from app.db.migrate import migrate  # local import: migrate.py imports this module
    migrate(db_path)
