"""Management commands for the Meeting Room Availability Tracker.

    python manage.py migrate      # create the database file and apply pending migrations
    python manage.py seed         # insert sample rooms and employees (safe to repeat)
    python manage.py runserver    # start the API on http://127.0.0.1:8000
"""
import argparse

from app.config import DB_PATH
from app.db.migrate import migrate
from app.db.seed import seed_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Meeting Room Tracker management commands")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="Create the database and apply pending migrations")
    sub.add_parser("seed", help="Insert sample rooms and employees (safe to repeat)")

    run = sub.add_parser("runserver", help="Start the API server")
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8000)
    run.add_argument("--no-reload", action="store_true", help="Disable auto-reload on code changes")

    args = parser.parse_args()

    if args.command == "migrate":
        applied = migrate()
        print(f"Database: {DB_PATH}")
        print("Applied: " + (", ".join(applied) if applied else "nothing, database is up to date"))
    elif args.command == "seed":
        seed_database()
        print("Sample data is in place.")
    elif args.command == "runserver":
        import uvicorn
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()
