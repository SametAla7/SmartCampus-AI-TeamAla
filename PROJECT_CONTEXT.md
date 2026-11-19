# SmartCampus AI — Project Context

## Purpose
SmartCampus AI is a university orientation and admissions platform for IIT / ISB and North American Private University. It provides candidate-facing flows and staff workspaces for admissions, interviews, academic review, direction, and administration. The project currently has a FastAPI backend and a React frontend built with Vite.

## Repository layout
- `app/api/`: FastAPI route modules, mounted under the configured `/api` prefix.
- `app/services/`: business logic used by API routes.
- `app/models/`: SQLAlchemy persistence models.
- `app/schemas/`: Pydantic request and response schemas.
- `app/core/`: settings, security helpers, and API errors.
- `app/db/`: SQLAlchemy base, engine, and session utilities.
- `frontend/src/components/layout/`: reusable React layout components (Navbar, Sidebar, Container). `frontend/src/pages/` is the location for React route views. Legacy Angular page source remains under `frontend/src/app/` and is not part of the Vite build.
- React API calls use `fetch` against the same-origin `/api` path.
- `frontend/src/main.jsx`: React bootstrap; `frontend/src/App.js`: route and layout composition.
- `tests/`: backend automated tests.
- `documentation_technique/`: technical project documentation.

## Main flows
The React app uses React Router and named Navbar, Sidebar, and Container components. Current route views include login and the workspace paths for dashboard, conversations, orientation, pre-registration, QCM, application dossier, academic review, interviews, direction, and administration. The frontend calls the backend under `/api`.

Backend routers cover authentication, users, study paths (`parcours`), conversations, applications (`candidatures`), interviews, documents, dashboard, and administration. Database and application options are defined in `app/core/config.py` and can be overridden with environment variables and the root `.env` file. Do not commit secrets from `.env`.

## Local development
- Frontend: `cd frontend`, `npm install`, then `npm start` (Vite dev server, normally http://localhost:5173); `npm run build` creates a production build.
- Backend: install dependencies from the repository's Python dependency manifest, configure the root `.env` using `.env.example`, then run `uvicorn app.main:app --reload` from the repository root. The API docs are available at `/docs` and the health endpoint at `/api/health`.

## Maintenance notes
Keep reusable React layout components under `frontend/src/components/layout/` and route views under `frontend/src/pages/`. Keep backend business logic in `app/services/` and transport handling in `app/api/`. Add React routes in `frontend/src/App.jsx`. This document describes the current structure; consult source/configuration for authoritative runtime behavior.

## GitHub automation
`.github/workflows/ci.yml` runs backend tests and the React/Vite production build on pushes and pull requests, with manual dispatch also available. After those checks succeed, pushes to any branch that contains this workflow publish backend and frontend images to GHCR. Images receive a sanitized branch tag and a commit SHA tag; `latest` is published only from the repository default branch. Pull request runs do not publish images. A branch must contain the workflow file for GitHub Actions to run it there.
## Docker deployment
- `compose.yaml` starts PostgreSQL, the FastAPI API, and the React/Vite frontend served by Nginx. Persistent volumes retain the database and uploaded documents.
- Local startup: `docker compose up --build -d`; open http://localhost:4200. API health: http://localhost:8000/api/health. Stop with `docker compose down` (data volumes remain); remove persisted data with `docker compose down -v`.
- Set `JWT_SECRET` and optionally `POSTGRES_PASSWORD` in the root `.env` before deployment. Defaults in Compose are intended only for local development.
- GitHub Actions publishes images on successful pushes from branches containing the Docker workflow. Use the branch tag when deploying a non-default branch; `latest` tracks the default branch. Authenticate to GHCR, set `BACKEND_IMAGE` and `FRONTEND_IMAGE` to the desired image tags on the Docker host, then run `docker compose pull && docker compose up -d`.
