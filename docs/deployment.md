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

Production uses automated Azure backups for `psql-manojasdyg-82692` (35-day retention, geo-redundant, point-in-time recovery), configured in [`infra/main.tf`](../infra/main.tf). The restore procedure and test log are in [RESTORE.md](RESTORE.md).

For local databases, take a manual copy:

```powershell
pg_dump -U meeting_app -h localhost -d meeting_rooms -F c -f meeting_rooms_backup.dump
```

Restore into an empty database with `pg_restore -U meeting_app -h localhost -d meeting_rooms meeting_rooms_backup.dump`.

## Azure deployment (Container Apps)

```
push to main
  -> CI                  tests, migration check, image build + /healthz smoke test
  -> Harbour Build       gitleaks, semgrep, trivy gate, then build and push images to ACR
  -> Deploy to Azure     roll both Container Apps to the new image, smoke test, roll back on failure
```

| Piece | Where |
|---|---|
| Database | Azure Database for PostgreSQL Flexible Server, private endpoint ([infra/main.tf](../infra/main.tf)) |
| Backend | Container App from `backend/Dockerfile`, port 8080 |
| Frontend | Container App from `frontend/Dockerfile` (nginx, port 8080) |
| Images | `<ACR_NAME>.azurecr.io/<owner>/<repo>:backend-<sha>` and `:frontend-<sha>` |

### One-time setup

1. Apply `infra/` with Terraform. Outputs `postgresql_host` and `postgresql_password` feed the next step.
2. Create the two Container Apps in the shared Container Apps Environment, with external ingress and the target port set to 8080.
3. Configure the backend (secrets and environment variables):

   ```bash
   export RESOURCE_GROUP=manojasdyg-82692 BACKEND_APP=manojasdyg-82692-backend
   export DB_HOST=<postgresql_host> DB_PASSWORD=<postgresql_password>
   export DJANGO_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
   export FRONTEND_ORIGIN=https://<frontend-fqdn>
   bash infra/azure/configure-backend.sh
   ```

4. In GitHub, add repository secrets `AZURE_CREDENTIALS` and `ACR_NAME`. Optionally add variables `AZURE_RESOURCE_GROUP`, `AZURE_BACKEND_APP`, `AZURE_FRONTEND_APP`. The defaults are `manojasdyg-82692`, `manojasdyg-82692-backend` and `manojasdyg-82692-frontend`.
5. Create a GitHub environment named `production`. Add required reviewers there to gate deployments.
6. Give the Container Apps pull access to the registry (`AcrPull` on the ACR for each app's managed identity).

### Backend environment

| Variable | Value on Azure |
|---|---|
| `DJANGO_DEBUG` | `0` |
| `DJANGO_SECRET_KEY` | Container App secret `django-secret-key` |
| `DJANGO_ALLOWED_HOSTS` | Backend ingress FQDN |
| `CORS_ALLOWED_ORIGINS` | Frontend origin, `https://...` |
| `CSRF_TRUSTED_ORIGINS` | `https://<backend-fqdn>` |
| `DJANGO_BEHIND_PROXY` | `1` (trusts `X-Forwarded-Proto`, sets secure cookies) |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` | Terraform outputs (`postgres` database, `psqladmin` user) |
| `DB_PASSWORD` | Container App secret `db-password` |
| `DB_SSLMODE` | `require` (Flexible Server enforces TLS) |
| `RUN_MIGRATIONS` | `1` (default). Set `0` to run `python manage.py migrate` as a separate release step |

The container applies migrations on start. The first run creates the `btree_gist` extension, which Terraform allow-lists through `azure.extensions`.

### Probes

| Path | Checks | Use |
|---|---|---|
| `/healthz` | Process is up, no database access | Liveness, Docker `HEALTHCHECK` |
| `/readyz` | Database reachable (503 otherwise) | Readiness |
| `/api/health` | API routing | Smoke test |

Both probes bypass `ALLOWED_HOSTS`, because Container Apps probes use the pod IP as Host.

### Rolling back

The deploy workflow records the running images before updating and restores them if the smoke test fails. To roll back by hand, run **Deploy to Azure** from the Actions tab with the SHA of a previously built commit.

## Before any shared or production use

The local setup is for development. Before other people use it:

- Set `DJANGO_DEBUG=0` and a real `DJANGO_SECRET_KEY`.
- Set `DJANGO_ALLOWED_HOSTS` to the real host name.
- Add authentication. The API currently has none, so anyone who can reach it can book, edit or cancel.
- Serve the frontend build (`npm run build`) behind HTTPS.
- Apply `infra/` for automated backups and test a restore following [RESTORE.md](RESTORE.md).
