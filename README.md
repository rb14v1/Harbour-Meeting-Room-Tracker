# Meeting Room Availability Tracker

An internal web app for checking meeting room availability, booking rooms for a date and time window, and managing reservations. Overlapping bookings are blocked on the server.

## Features

- **Dashboard**: room counts, availability now, bookings for the day, upcoming meetings, recent activity.
- **Room availability**: pick a date and time window, filter by capacity, name and facilities.
- **Booking**: validated form with live room details. Back-to-back meetings allowed, overlaps rejected.
- **Bookings**: all, upcoming, past and cancelled views. Search by employee, filter by room and date, cancel, view details.
- **Room management**: add, edit, deactivate or remove rooms. Rooms with history are deactivated, not deleted.
- **Reports**: daily and weekly counts, most booked room, utilisation, employee statistics.

## Stack

- Backend: Python 3.13, FastAPI, Pydantic, `sqlite3`
- Frontend: React 18, Vite, React Router, Bootstrap 5
- Database: SQLite (`backend/data/meeting_rooms.db`), created and seeded on first start
- Deployment: Docker Compose (nginx + API)

## Quick start

### Docker

```powershell
copy .env.example .env
docker compose up --build -d
```

Open <http://localhost:8080>.

### Local development

```powershell
# Backend
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate      # creates data\meeting_rooms.db and applies migrations
python manage.py seed         # optional: sample rooms and employees
python manage.py runserver    # API on http://127.0.0.1:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

Schema changes live in `backend\app\db\migrations\` as numbered files (`0002_name.sql`, and so on). `migrate` applies only the ones not yet recorded in `schema_migrations`.

## Tests and checks

```powershell
cd backend
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -q                     # 20 tests: booking rules, concurrency, availability, rooms, reports

cd ..
python healthz.py             # API and database health
```

## Repository layout

```
.github/workflows/   CI: backend tests and frontend build
backend/             FastAPI app, schema, seed data, tests
frontend/            React + Vite SPA
infra/               Dockerfiles and nginx config
docs/                Architecture, booking rules, API, deployment
healthz.py           Health check script
docker-compose.yml   Multi-container setup
```

## Documentation

- [Architecture](docs/architecture.md)
- [Booking rules](docs/booking-rules.md)
- [API reference](docs/api.md)
- [Deployment](docs/deployment.md)

## Known limitations

- No authentication. Put SSO in front of the app before wider rollout.
- SQLite is single-node. Suitable for one office, not for multi-instance deployment.
- Room and booking times use the server's local clock.
