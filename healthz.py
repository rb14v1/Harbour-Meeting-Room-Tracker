"""Health check for the Meeting Room Availability Tracker.

Usage:
    python healthz.py                       # checks http://localhost:8000 and the database file
    python healthz.py --api http://localhost:8080/api
    python healthz.py --db backend/data/meeting_rooms.db

Exit code 0 when every check passes, 1 otherwise.
"""
import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "backend" / "data" / "meeting_rooms.db"


def check_api(base: str) -> tuple[bool, str]:
    url = base.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            ok = resp.status == 200 and body.get("status") == "ok"
            return ok, f"API {url} -> {resp.status} {body}"
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return False, f"API {url} unreachable: {exc}"


def check_db(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"Database not found at {path} (it is created on first backend start)"
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = {"rooms", "employees", "bookings"} - tables
            if missing:
                return False, f"Database missing tables: {sorted(missing)}"
            rooms = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            return True, f"Database {path.name} OK ({rooms} rooms)"
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return False, f"Database check failed: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Health check for the room tracker.")
    parser.add_argument("--api", default="http://localhost:8000/api",
                        help="API base URL (default: http://localhost:8000/api)")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to meeting_rooms.db")
    parser.add_argument("--skip-api", action="store_true", help="Only check the database")
    args = parser.parse_args()

    results = []
    if not args.skip_api:
        results.append(check_api(args.api))
    results.append(check_db(Path(args.db)))

    failed = False
    for ok, message in results:
        print(("[PASS] " if ok else "[FAIL] ") + message)
        failed = failed or not ok
    print("Overall:", "HEALTHY" if not failed else "UNHEALTHY")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
