import sqlite3

import pytest

from app.db import migrate as migrate_module
from app.db.migrate import MIGRATIONS_DIR, migrate


def _tables(db):
    conn = sqlite3.connect(db)
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def test_fresh_database_gets_all_tables_and_is_recorded(tmp_path):
    db = tmp_path / "fresh.db"
    assert migrate(db) == ["0001_initial.sql"]
    assert {"rooms", "employees", "bookings", "schema_migrations"} <= _tables(db)
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT version, name FROM schema_migrations").fetchall() == [(1, "initial")]
    conn.close()


def test_migrate_is_idempotent(tmp_path):
    db = tmp_path / "again.db"
    migrate(db)
    assert migrate(db) == []


def test_legacy_database_is_upgraded_without_losing_data(tmp_path):
    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(db)
    conn.executescript((MIGRATIONS_DIR / "0001_initial.sql").read_text(encoding="utf-8"))
    conn.execute("INSERT INTO rooms (room_name, location, capacity) VALUES ('Keep Me', 'Floor 1', 5)")
    conn.commit()
    conn.close()

    assert migrate(db) == ["0001_initial.sql"]

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT room_name FROM rooms").fetchall() == [("Keep Me",)]
    conn.close()


def test_failed_migration_rolls_back(tmp_path, monkeypatch):
    folder = tmp_path / "migrations"
    folder.mkdir()
    (folder / "0001_initial.sql").write_text(
        "CREATE TABLE good (id INTEGER PRIMARY KEY);", encoding="utf-8")
    (folder / "0002_broken.sql").write_text(
        "CREATE TABLE half_done (id INTEGER PRIMARY KEY);\nINSERT INTO no_such_table VALUES (1);",
        encoding="utf-8")
    monkeypatch.setattr(migrate_module, "MIGRATIONS_DIR", folder)

    db = tmp_path / "broken.db"
    with pytest.raises(sqlite3.Error):
        migrate(db)

    tables = _tables(db)
    assert "good" in tables
    assert "half_done" not in tables
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT version FROM schema_migrations").fetchall() == [(1,)]
    conn.close()
