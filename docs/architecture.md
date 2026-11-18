# Architecture

## Components

| Layer | Technology | Location |
|---|---|---|
| Frontend | React 18, Vite 5, React Router 6, Bootstrap 5.3 | `frontend/` |
| Backend API | FastAPI 0.115, Pydantic 2, Python 3.13 | `backend/app/` |
| Database | SQLite via `sqlite3` (WAL mode, foreign keys on) | `backend/data/meeting_rooms.db` |
| Reverse proxy (Docker) | nginx 1.27 | `infra/nginx.conf` |

## Request flow

```
Browser ──> frontend (Vite dev :5173 or nginx :8080)
              │  /api/* proxied
              ▼
          FastAPI (:8000)  ── routers/api.py
              │
              ▼
          services/        rooms.py, bookings.py, reports.py
              │
              ▼
          database.py      read_connection() / write_transaction()
              │
              ▼
          SQLite file
```

## Backend layout

- `app/main.py`: app factory, CORS, validation error format, startup (schema + seed).
- `app/routers/api.py`: REST endpoints under `/api`.
- `app/schemas.py`: request validation (Pydantic).
- `app/services/`: business rules. Overlap detection lives in `services/bookings.py`.
- `app/database.py`: connection handling. `write_transaction()` issues `BEGIN IMMEDIATE`.
- `app/db/schema.sql`: idempotent schema (`CREATE ... IF NOT EXISTS`).
- `app/db/seed.py`: sample rooms and employees, `INSERT OR IGNORE` so restarts never duplicate.

## Concurrency

Writes run under `BEGIN IMMEDIATE`, which takes SQLite's write lock before the overlap query. Two requests cannot both pass the check for the same slot. `tests/test_bookings.py::test_concurrent_bookings_for_same_slot_only_one_succeeds` exercises this with 8 threads.

## Data model

See [`booking-rules.md`](booking-rules.md) for overlap, cancellation and validation rules. Indexes are on `bookings(room_id, booking_date, status)`, `bookings(booking_date, status)`, `bookings(employee_id)` and `bookings(created_at)`.
