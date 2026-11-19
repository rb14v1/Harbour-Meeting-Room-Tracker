# Architecture

## Components

| Layer | Technology | Location |
|---|---|---|
| Frontend | React 18, Vite 5, React Router 6, Bootstrap 5.3 | `frontend/` |
| Backend API | Django 5.1, Django REST Framework 3.15, django-cors-headers 4.6 | `backend/` |
| Database | PostgreSQL 18 (local install) via psycopg 3.2 | database `meeting_rooms` |
| Settings | python-dotenv loads `backend\.env` | `backend/config/settings.py` |

## Request flow

```
Browser ──> Vite dev server (:5173)
              │  /api/* proxied to 127.0.0.1:8000
              ▼
          Django (runserver :8000)
              │  config/urls.py  →  meetings/urls.py  (prefix /api/)
              ▼
          meetings/views.py      DRF APIViews: parse input, return JSON
              │
              ▼
          meetings/serializers.py   validate request data, shape responses
              │
              ▼
          meetings/services.py   booking rules, overlap checks, locking
          meetings/reports.py    dashboard and report aggregates
              │
              ▼
          Django ORM  →  PostgreSQL
```

## Backend layout

| Path | Purpose |
|---|---|
| `config/settings.py` | Database, installed apps, CORS, DRF settings, `.env` loading |
| `config/urls.py` | Mounts `meetings` under `/api/` |
| `meetings/models.py` | `Employee`, `Room`, `Booking` with constraints and indexes |
| `meetings/services.py` | Create, edit, cancel and list bookings; availability calculation |
| `meetings/reports.py` | Dashboard summary and report statistics |
| `meetings/serializers.py` | Input validation (names, times, facilities) and response shapes |
| `meetings/views.py` | Endpoints. Each maps to one URL in `meetings/urls.py` |
| `meetings/exceptions.py` | 409 and 422 error types. Converts validation errors to `{"detail": [{field, message}]}` |
| `meetings/management/commands/seed.py` | Sample rooms, employees and demo bookings. Safe to repeat |
| `meetings/migrations/` | Django migrations. `0001_initial` also enables `btree_gist` |
| `meetings/tests/` | API rule tests, room and availability tests, and the concurrency test |

## Concurrency and overlap protection

Two layers prevent double-booking a room:

1. **Application lock.** `services._save_booking` runs inside `transaction.atomic()` and locks the room row with `select_for_update()`. Concurrent bookings for the same room run one at a time, and the overlap query sees the committed result.
2. **Database constraint.** The `Booking` model has an `ExclusionConstraint` on `(room, tsrange(booking_date + start_time, booking_date + end_time))`, using `&&`, for rows where `status = 'Confirmed'`. PostgreSQL rejects an overlapping row even if the application check is skipped. The service converts that rejection into a 409.

`meetings/tests/test_concurrency.py` starts 8 threads against the same slot on the real database and expects exactly one success.

## Data model

| Table | Key columns | Constraints |
|---|---|---|
| `employees` | `employee_id` (PK), `employee_name`, `email` | `email` unique |
| `rooms` | `room_id` (PK), `room_name`, `location`, `capacity`, `facilities`, `status` | `room_name` unique; `capacity > 0`; status `Active` or `Inactive` |
| `bookings` | `booking_id` (PK), `room_id` (FK), `employee_id` (FK), `meeting_title`, `booking_date`, `start_time`, `end_time`, `status`, `created_at` | `end_time > start_time`; no overlapping confirmed bookings per room; FKs use `PROTECT` |

Indexes on `bookings`: `(room_id, booking_date, status)` and `(booking_date, status)`.

Business rules are in [booking-rules.md](booking-rules.md).
