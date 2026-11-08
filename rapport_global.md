# Rapport global – SmartCampus AI

## 1. Backend (réellement développé)
- **Techno/archi.** : Python, FastAPI, SQLAlchemy, Pydantic ; structure `app/` (api, core, models, schemas, services, db).
- **API** : routeurs `auth`, `users`, `parcours`, `conversations`, `candidatures`, `entretiens`, `documents`, `dashboard`, `admin` (préfixe `/api`) ; `/api/health`, `/docs`.
- **Auth/sécurité** : JWT (access/refresh), hachage Argon2, rôles (`CANDIDAT`, responsables, direction, admin) ; inscription publique `POST /api/auth/register` (rôle candidat), login, refresh, `/auth/me`.

## 2. Frontend (réellement développé)
- **Techno** : Angular 19 (standalone), TypeScript, HttpClient + intercepteur auth, routing.
- **Interfaces/pages** : page login/inscription (`LoginComponent`, mode login/signup) et `DashboardComponent` (accueil après connexion, déconnexion) ; redirections `/login` et `/dashboard`.
- **Communication** : appels API FastAPI (config dev `http://127.0.0.1:8001/api`) pour auth/inscription et session utilisateur.

## 3. Base de données et hébergement
- **SGBD** : PostgreSQL hébergé sur **Prisma Postgres** (distant), accès via SQLAlchemy + driver `psycopg` v3 ; config `.env`/variables d’environnement, garde anti SQLite/local en exécution normale.
- **Tables/modèles principaux** : `users`, `candidatures`, `parcours`, `conversations`, `messages`, `qcms`, `entretiens`, `documents`, `demandes_complement`, décisions liées aux candidatures.

## État actuel et reste à faire
- **État** : socle backend/frontend opérationnel, auth et persistance utilisateurs vérifiées sur Prisma ; tests backend automatisés existants (36) passants.
- **À développer/compléter** : interfaces métier complètes (parcours, candidatures, entretiens, documents, dashboard/admin avancés), chatbot/RAG (prévu mais non opérationnel), migrations Alembic, et couverture E2E/UI.