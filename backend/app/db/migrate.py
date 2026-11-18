import re
from pathlib import Path

from app.config import DB_PATH, MIGRATIONS_DIR
from app.database import get_connection

FILE_PATTERN = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")


def available_migrations(directory: Path = None) -> list[tuple[int, str, Path]]:
    directory = directory or MIGRATIONS_DIR
    found = []
    for path in directory.glob("*.sql"):
        match = FILE_PATTERN.match(path.name)
        if not match:
            raise RuntimeError(f"Migration file '{path.name}' must be named NNNN_description.sql")
        found.append((int(match.group(1)), match.group(2), path))
    return sorted(found)


def migrate(db_path=DB_PATH) -> list[str]:
    """Apply every migration not yet recorded in schema_migrations. Returns the names applied."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    INTEGER PRIMARY KEY,
                name       TEXT    NOT NULL,
                applied_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
            )
            """
        )
        done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        applied = []
        for version, name, path in available_migrations():
            if version in done:
                continue
            # Name comes from a validated filename, so the f-string is safe here.
            script = (
                "BEGIN;\n"
                f"{path.read_text(encoding='utf-8')}\n"
                f"INSERT INTO schema_migrations (version, name) VALUES ({version}, '{name}');\n"
                "COMMIT;"
            )
            try:
                conn.executescript(script)
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
            applied.append(path.name)
        return applied
    finally:
        conn.close()
