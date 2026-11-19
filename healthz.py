"""Health check for the Meeting Room Availability Tracker.

Usage:
    python healthz.py                              # API on http://127.0.0.1:8000/api and PostgreSQL
    python healthz.py --api http://127.0.0.1:8000/api --skip-db

Database settings are read from backend\\.env (or the environment): DB_NAME, DB_USER,
DB_PASSWORD, DB_HOST, DB_PORT.

Exit code 0 when every check passes, 1 otherwise.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _load_env() -> None:
    for env_file in (ROOT / ".env", ROOT / "backend" / ".env"):
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def check_api(base: str) -> tuple[bool, str]:
    url = base.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            ok = resp.status == 200 and body.get("status") == "ok"
            return ok, f"API {url} -> {resp.status} {body}"
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return False, f"API {url} unreachable: {exc}"


def check_db() -> tuple[bool, str]:
    try:
        import psycopg
    except ImportError:
        return False, "psycopg is not installed. Activate backend\\.venv and run pip install -r requirements.txt"

    name = os.getenv("DB_NAME", "meeting_rooms")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    try:
        with psycopg.connect(
            dbname=name, user=os.getenv("DB_USER", "meeting_app"), password=os.getenv("DB_PASSWORD", ""),
            host=host, port=port, connect_timeout=5,
        ) as conn:
            rooms = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            return True, f"PostgreSQL {name}@{host}:{port} OK ({rooms} rooms)"
    except psycopg.OperationalError as exc:
        return False, f"PostgreSQL {name}@{host}:{port} unreachable: {str(exc).strip()}"
    except psycopg.errors.UndefinedTable:
        return False, f"PostgreSQL {name} has no tables yet. Run: python manage.py migrate"


def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(description="Health check for the room tracker.")
    parser.add_argument("--api", default="http://127.0.0.1:8000/api",
                        help="API base URL (default: http://127.0.0.1:8000/api)")
    parser.add_argument("--skip-db", action="store_true", help="Only check the API")
    args = parser.parse_args()

    results = [check_api(args.api)]
    if not args.skip_db:
        results.append(check_db())

    failed = False
    for ok, message in results:
        print(("[PASS] " if ok else "[FAIL] ") + message)
        failed = failed or not ok
    print("Overall:", "HEALTHY" if not failed else "UNHEALTHY")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
