import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("MRT_DB_PATH", BASE_DIR / "data" / "meeting_rooms.db"))
MIGRATIONS_DIR = BASE_DIR / "app" / "db" / "migrations"
CORS_ORIGINS = [o.strip() for o in os.getenv("MRT_CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if o.strip()]
WORK_START = "08:00"
WORK_END = "18:00"
