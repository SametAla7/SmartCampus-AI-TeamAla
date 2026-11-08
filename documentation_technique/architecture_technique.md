# Architecture technique — SmartCampus AI

> Basé sur l’analyse du code source du dépôt (backend FastAPI/SQLAlchemy, frontend Angular 19, configuration Prisma PostgreSQL). Aucun secret ni identifiant n’est inclus.

## 1. Vue d’ensemble

```mermaid
flowchart LR
  U[Utilisateur / Navigateur] -->|HTTP/JSON, JWT Bearer| FE[Frontend Angular 19]
  FE -->|REST /api/*| BE[Backend FastAPI]
  BE -->|SQLAlchemy ORM + psycopg v3| DB[(PostgreSQL hébergé\nPrisma Postgres)]
  BE -->|Lecture/écriture binaire\n(métadonnées en DB)| FS[(Stockage fichiers\nchemin local configuré)]
  BE -.->|Intégration préparée\n(non opérationnelle)| LLM[LLM / RAG externe]
  ADM[Admin] --> FE
```

## 2. Composants techniques

| Composant | Rôle | Technologies / bibliothèques (réelles) | Justification (observée / adaptée) | Communication |
|---|---|---|---|---|
| **Frontend** | Interface web : connexion/inscription candidat, dashboard, appels API authentifiés. | Angular 19 (standalone), TypeScript, `@angular/common/http`, `Router`, intercepteur HTTP JWT (`authInterceptor`). | Framework structuré pour SPA ; HttpClient/intercepteur simplifient l’auth Bearer et le routage. | Appelle le backend REST (`/api/*`) sur l’instance FastAPI configurée (dev : port 8001). |
| **Backend API** | Logique métier, validation, sécurité, exposition REST. | Python, **FastAPI**, Pydantic (schémas), SQLAlchemy (ORM), services `app/services/*`, dépendances `app/api/deps.py` (JWT + rôles). | FastAPI offre validation, OpenAPI (`/docs`), dépendances et performance adaptées à une API REST. | Reçoit HTTP/JSON du frontend ; utilise `get_db`/SQLAlchemy vers PostgreSQL ; gère fichiers via services ; appelle la couche chatbot/RAG si configurée. |
| **Base de données** | Persistance des utilisateurs, candidatures, parcours, conversations/messages, documents (métadonnées), QCM, entretiens, demandes de complément, décisions. | **PostgreSQL hébergé sur Prisma Postgres**, SQLAlchemy, driver **`psycopg` v3** (préféré), config `.env`/variables, garde anti SQLite/local en exécution normale. | PostgreSQL relationnel adapté aux relations métier ; hébergement distant géré ; SQLAlchemy conserve le modèle ORM Python. | Backend ↔ DB via sessions SQLAlchemy (`SessionLocal`/`get_db`) ; `scripts/check_db.py` et FastAPI partagent la même résolution effective. |
| **Stockage des fichiers** | Stockage binaire des documents de candidature (hors base) ; métadonnées en table `documents`. | Système de fichiers local via `DOCUMENT_STORAGE_PATH` (config), `uuid` pour clé de stockage, `UploadFile` FastAPI, `FileResponse` au téléchargement. | Sépare binaire (fichiers) et métadonnées (DB) ; simple à exploiter en dev. **Limite** : stockage local, non objet distant (S3, etc.) non implémenté. | Upload via API candidature ; enregistrement métadonnées + binaire ; téléchargement contrôlé via `GET /api/documents/{id}/download` après contrôle d’accès. |
| **LLM / Chatbot** | Réponse conversationnelle aux candidats (prévue). | `CHATBOT_ENABLED/PROVIDER/API_KEY` en config ; `chatbot_service.is_chatbot_configured()` ; `generate_reply()` lève `503 CHATBOT_NOT_CONFIGURED` si non configuré (pas de réponse simulée). | Évite les réponses fictives ; intégration LLM branchable par configuration. | Appelé par `POST /api/conversations/{id}/messages` **uniquement** si configuré ; sinon erreur explicite. |
| **RAG / traitements IA automatiques** | Préparation indexation/recherche documentaire pour assistance IA. | `app/services/rag_service.py`, endpoints admin `/api/admin/rag/reindex` et `/api/admin/rag/status` ; config `RAG_*`. | Sépare administration RAG des conversations ; statut/reindex exposés aux admins. | Admin → FastAPI → service RAG ; interaction LLM/RAG **non opérationnelle** par défaut (configuration requise). |

## 3. Flux principaux
- **Authentification** : Angular → `POST /api/auth/login` → JWT ; requêtes suivantes avec `Authorization: Bearer <token>`.
- **Inscription candidat** : Angular → `POST /api/auth/register` → FastAPI/SQLAlchemy → PostgreSQL Prisma (compte candidat, mot de passe Argon2).
- **Dossier candidature** : candidat crée candidature, consulte QCM/demandes ; dépôt document = upload multipart → contrôle taille/extension → fichier sur `DOCUMENT_STORAGE_PATH` + métadonnées en DB.
- **Conversation** : création/listing réservés selon règles ; envoi message déclenche réponse chatbot **si configuré**, sinon `503`.

## 4. État des composants (synthèse)
| Composant | Statut |
|---|---|
| Backend FastAPI, routes REST, auth JWT/Argon2, rôles | **Implémenté** ; tests automatisés backend existants passants (suite connue : 36 tests) — couverture non exhaustive runtime. |
| PostgreSQL Prisma + SQLAlchemy/psycopg v3 | **Implémenté et fonctionnel** pour la configuration vérifiée (connexion, persistance testée). |
| Stockage fichiers local + métadonnées | **Implémenté** (chemin configurable) ; **non vérifié** en environnement distant/objet. |
| Chatbot LLM | **Implémenté (structure/garde)** mais **non opérationnel** sans configuration/provider. |
| RAG / indexation | **Implémenté (endpoints/statut/service)** ; **opérationnalité dépendante** de la configuration/corpus. |