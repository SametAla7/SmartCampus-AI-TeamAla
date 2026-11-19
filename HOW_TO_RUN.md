# How to Run SmartCampus AI

This guide is for a fresh checkout on Windows, macOS, or Linux. The recommended setup runs the frontend, API, and database together with Docker Compose.

## Requirements

- Git
- Docker Desktop (Windows/macOS) or Docker Engine with the Docker Compose plugin (Linux)
- An internet connection for the first build, so Docker can download base images and packages

## 1. Get the project

```bash
git clone https://github.com/SametAla7/SmartCampus-AI-TeamAla.git
cd SmartCampus-AI-TeamAla
```

If you already have the project, open a terminal in its root folder (the folder containing `compose.yaml`).

## 2. Configure local environment

Copy `.env.example` to `.env` in the project root. Set a local JWT secret and, if desired, a PostgreSQL password. For local use, Compose supplies a development database and has fallback values for both.

PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Do not commit `.env`. The Compose stack uses its own PostgreSQL container; you do not need a separately installed database or a hosted `DATABASE_URL`.

## 3. Build and start the application

Make sure Docker Desktop is running, then run from the project root:

```bash
docker compose up --build -d
```

The first build may take several minutes. Compose waits for PostgreSQL and the API health checks before starting the frontend.

Open these URLs when the containers are healthy:

- Frontend: <http://localhost:4200>
- API health: <http://localhost:8000/api/health>
- Interactive API documentation: <http://localhost:8000/docs>

The frontend proxies `/api` requests to the backend container. The database and uploaded documents persist in Docker volumes across restarts.

## Useful Docker commands

Run these from the project root:

```bash
# Check container status
docker compose ps

# Follow all service logs
docker compose logs -f

# Follow only backend logs
docker compose logs -f backend

# Stop the services; keep database and uploaded files
docker compose down

# Start them again
docker compose up -d
```

To erase the saved database and uploaded documents as well as stop the services, run `docker compose down -v`. This permanently deletes the volumes' data.

## Build the Angular frontend without Docker

The frontend uses Angular 19 and Node.js. From the project root:

```bash
cd frontend
npm ci
npm run build
```

To run the Angular development server, use `npm start`. The complete app is easiest to run with Docker Compose because Compose also configures the API proxy and database.

## Run backend tests

Python 3.12 is used in CI. From the project root, install dependencies and run pytest:

```bash
python -m venv .venv
```

Activate the environment, then install the packages:

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:APP_ENV = "test"
$env:SMARTCAMPUS_ALLOW_NON_REMOTE_DB = "1"
python -m pytest -q
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
APP_ENV=test SMARTCAMPUS_ALLOW_NON_REMOTE_DB=1 python -m pytest -q
```

The tests use an isolated in-memory SQLite database; they do not require the Compose database.

## Troubleshooting

- **Docker commands cannot connect:** start Docker Desktop and wait until its engine reports that it is running.
- **A port is already in use:** stop the process using port `4200` or `8000`, or change the corresponding host port in `compose.yaml`.
- **A container is unhealthy:** check `docker compose ps` and `docker compose logs backend db` for the startup error.
- **Want a clean rebuild:** run `docker compose down` followed by `docker compose up --build -d`.
- **Login fails after a reset:** create/register a user through the app again. User accounts are stored in the PostgreSQL volume and are removed by `docker compose down -v`.
