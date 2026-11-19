# Deployment and Local Setup

This project runs locally on Windows with a local PostgreSQL install. A Docker setup is also provided for Linux-style deployment; see [Docker](#docker-optional).

## Prerequisites

| Software | Version | Check |
|---|---|---|
| Python | 3.13 | `py -3.13 --version` |
| Node.js | 24 LTS | `node --version` |
| PostgreSQL | 17 or 18 | `psql --version` |

## First-time setup

### 1. Create the database user and database

Open **SQL Shell (psql)**, log in as `postgres`, and run:

```sql
CREATE ROLE meeting_app LOGIN PASSWORD 'your-password' CREATEDB;
CREATE DATABASE meeting_rooms OWNER meeting_app;
```

`CREATEDB` lets Django create a `test_meeting_rooms` database for the test suite.

### 2. Configure the backend

```powershell
cd backend
copy .env.example .env
```

Set these values in `backend\.env`:

| Variable | Meaning |
|---|---|
| `DB_PASSWORD` | Password for `meeting_app` |
| `DJANGO_SECRET_KEY` | Long random text. Do not share it |
| `DB_NAME`, `DB_USER`, `DB_HOST`, `DB_PORT` | Defaults match the setup above |

### 3. Install backend packages

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

### 4. Install frontend packages

```powershell
cd frontend
npm install
```

## Running the app

Terminal 1, backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed        # optional sample data
python manage.py runserver   # http://127.0.0.1:8000
```

Terminal 2, frontend:

```powershell
cd frontend
npm run dev                  # http://localhost:5173
```

Vite forwards `/api` requests to port 8000, so the backend must be running.

## Verifying

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py check
python manage.py test        # 34 tests
cd ..
python healthz.py            # API and PostgreSQL health
```

`healthz.py` reads `backend\.env` and exits with code 0 when both checks pass.

## Database changes

Models live in `backend\meetings\models.py`. After editing a model:

```powershell
cd backend
python manage.py makemigrations meetings
python manage.py migrate
```

Commit the new file in `meetings\migrations\` with the model change.

## Docker (optional)

Requires Docker Desktop. Compose starts PostgreSQL 17, the Django API under gunicorn, and the React build behind nginx.

```powershell
cd C:\Users\admin\meeting-room-tracker
docker compose up --build -d
docker compose exec backend python manage.py seed     # optional sample data
```

Open http://localhost:8080. The `pgdata` volume keeps the database between restarts.

Each container start runs `migrate`. Settings come from `backend\.env`, so set `DB_PASSWORD` and `DJANGO_SECRET_KEY` there first. Compose overrides `DB_HOST=db` and `DJANGO_DEBUG=0` inside the containers.

Stop with `docker compose down`. Add `-v` to also delete the database volume.

## Backups

```powershell
pg_dump -U meeting_app -h localhost -d meeting_rooms -F c -f meeting_rooms_backup.dump
```

Restore into an empty database with `pg_restore -U meeting_app -h localhost -d meeting_rooms meeting_rooms_backup.dump`.

## Before any shared or production use

The local setup is for development. Before other people use it:

- Set `DJANGO_DEBUG=0` and a real `DJANGO_SECRET_KEY`.
- Set `DJANGO_ALLOWED_HOSTS` to the real host name.
- Serve Django with a production WSGI server such as gunicorn. It is not in `requirements.txt` yet.
- Add authentication. The API currently has none, so anyone who can reach it can book, edit or cancel.
- Serve the frontend build (`npm run build`) behind HTTPS.
- Schedule `pg_dump` backups.
