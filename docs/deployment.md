# Deployment

## Docker (recommended)

1. Copy `.env.example` to `.env`. `docker-compose.yml` requires it.
2. From the repo root:

   ```powershell
   docker compose up --build -d
   ```

3. Open `http://localhost:8080`. The API is reachable through nginx at `/api`.
4. Check health:

   ```powershell
   python healthz.py --api http://localhost:8080/api --db data/meeting_rooms.db
   ```

The database lives in `./data/meeting_rooms.db` on the host, mounted into the backend container. Back up that file to back up all data.

## Local (without Docker)

Backend:

```powershell
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (second terminal):

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` to port 8000.

## Tests

```powershell
cd backend
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -q
```

## Production notes

- The SQLite file is single-node storage. Do not run multiple backend replicas against one file on a network share.
- Put TLS and authentication in front of nginx. The app has no login. Add SSO at the reverse proxy before exposing it beyond the internal network.
- Set `MRT_CORS_ORIGINS` to the real frontend origin.
