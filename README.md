# Meeting Room Availability Tracker

An internal web app for checking meeting room availability, booking rooms for a date and time window, and managing reservations. Overlapping bookings are blocked by the database itself.

## Features

- **Dashboard**: room counts, availability now, bookings for the day, upcoming meetings, recent activity.
- **Room availability**: pick a date and time window, filter by capacity, name and facilities.
- **Booking**: validated form. Back-to-back meetings allowed, overlaps rejected. Names accept English letters and single spaces only.
- **Bookings**: all, upcoming, past and cancelled views. Search by employee, filter by room and date, edit or cancel upcoming bookings, view details.
- **Room management**: add, edit, deactivate or remove rooms. Rooms with history are deactivated, not deleted.
- **Reports**: daily and weekly counts, most booked room, utilisation, employee statistics.

## Stack

- Backend: Python 3.13, Django 5.1, Django REST Framework, psycopg 3
- Database: PostgreSQL 17 or newer (local install)
- Frontend: React 18, Vite, React Router, Bootstrap 5

## One-time setup

### 1. PostgreSQL

Install PostgreSQL from postgresql.org and remember the `postgres` superuser password. Then open **SQL Shell (psql)** and run:

```sql
CREATE ROLE meeting_app LOGIN PASSWORD 'choose-a-password' CREATEDB;
CREATE DATABASE meeting_rooms OWNER meeting_app;
```

`CREATEDB` lets Django create a separate test database when you run `manage.py test`.

### 2. Backend settings

```powershell
cd backend
copy .env.example .env
```

Open `backend\.env` and set `DB_PASSWORD` to the password you chose. Set `DJANGO_SECRET_KEY` to any long random text.

### 3. Python and packages

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

## Run

Backend (terminal 1):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py migrate      # creates the tables in PostgreSQL
python manage.py seed         # optional: sample rooms, employees and bookings
python manage.py runserver    # API on http://127.0.0.1:8000
```

Frontend (terminal 2):

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py test
```

Django creates and destroys a `test_meeting_rooms` database. Your `meeting_rooms` data is not touched.

Health check, with the API running:

```powershell
cd ..
python healthz.py
```

## Migrations

Schema lives in `backend\meetings\models.py`. After changing a model:

```powershell
python manage.py makemigrations meetings
python manage.py migrate
```

The first migration also enables the `btree_gist` extension, which the overlap constraint needs.

## Repository layout

```
backend/
  config/            Django settings and URL routing
  meetings/          models, services (booking rules), serializers, views, seed command, tests
frontend/            React + Vite single-page app
docs/                Architecture, booking rules, API reference
healthz.py           API and database health check
```

`infra/` and `docker-compose.yml` run the same stack in containers (PostgreSQL, gunicorn, nginx). Local development doesn't need them. See [deployment](docs/deployment.md#docker-optional).

Azure Container Apps deployment, pipelines and rollback: [deployment](docs/deployment.md#azure-deployment-container-apps).

## Documentation

- [Architecture](docs/architecture.md)
- [Booking rules](docs/booking-rules.md)
- [API reference](docs/api.md)

## Known limitations

- No authentication. Add SSO before exposing the app beyond the internal network.
- Times use the server's local clock (`APP_TIME_ZONE`).
