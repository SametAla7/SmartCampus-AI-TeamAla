# SmartCampus AI — Project Context

## Purpose
SmartCampus AI is a university orientation and admissions platform for IIT / ISB and North American Private University. It provides candidate-facing flows and staff workspaces for admissions, interviews, academic review, direction, and administration. The project currently has a FastAPI backend and an Angular standalone frontend.

## Repository layout
- `app/api/`: FastAPI route modules, mounted under the configured `/api` prefix.
- `app/services/`: business logic used by API routes.
- `app/models/`: SQLAlchemy persistence models.
- `app/schemas/`: Pydantic request and response schemas.
- `app/core/`: settings, security helpers, and API errors.
- `app/db/`: SQLAlchemy base, engine, and session utilities.
- `frontend/src/app/<page>/`: one folder per Angular page; each page keeps its component TypeScript, HTML template, and CSS together.
- `frontend/src/app/services/`: shared frontend API/auth services and the auth interceptor.
- `frontend/src/main.ts`: standalone bootstrap and lazy route table.
- `tests/`: backend automated tests.
- `documentation_technique/`: technical project documentation.

## Main flows
Frontend pages include login/signup, dashboard, conversations, orientation, pre-registration, QCM, application dossier, academic review, interview management, direction, and administration. Angular routes lazy-load each page. The auth interceptor attaches a bearer token when available. The frontend calls the backend under `/api`.

Backend routers cover authentication, users, study paths (`parcours`), conversations, applications (`candidatures`), interviews, documents, dashboard, and administration. Database and application options are defined in `app/core/config.py` and can be overridden with environment variables and the root `.env` file. Do not commit secrets from `.env`.

## Local development
- Frontend: `cd frontend`, `npm install`, then `npm start` (Angular dev server, normally http://localhost:4200); `npm run build` creates a production build.
- Backend: install dependencies from the repository's Python dependency manifest, configure the root `.env` using `.env.example`, then run `uvicorn app.main:app --reload` from the repository root. The API docs are available at `/docs` and the health endpoint at `/api/health`.

## Maintenance notes
Keep each page's template and styles in its page folder. Put reusable frontend HTTP/auth behavior in `frontend/src/app/services/`; keep backend business logic in `app/services/` and transport handling in `app/api/`. Update `frontend/src/main.ts` when adding or moving a lazy page route. This document describes the current structure; consult source/configuration for authoritative runtime behavior.

## GitHub automation
`.github/workflows/ci.yml` runs backend tests and the Angular production build on pushes, pull requests, and manual runs. A push to the default branch also builds and publishes backend and frontend Docker images to GHCR, tagged `latest` and with the commit SHA.

## Docker deployment
- `compose.yaml` starts the FastAPI API and Angular/Nginx frontend. The backend requires `DATABASE_URL_DIRECT` in the root `.env` and connects to the hosted PostgreSQL database; uploaded documents are stored in a persistent volume.
- Startup: `docker compose up --build -d`; open http://localhost:4200. API health: http://localhost:8000/api/health. Stop with `docker compose down`; uploaded documents remain in their volume.
- GitHub Actions runs CI on pushes and pull requests. A push to the repository's default branch builds and publishes `ghcr.io/<owner>/<repo>-backend` and `ghcr.io/<owner>/<repo>-frontend` with branch and commit SHA tags; `latest` is reserved for the default branch. To deploy on a Docker host, authenticate to GHCR, set `BACKEND_IMAGE` and `FRONTEND_IMAGE` to those image names in the host environment, then run `docker compose pull && docker compose up -d`.
