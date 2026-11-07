# Conception des API — SmartCampus AI

> Analyse fondée sur les routes FastAPI (`app/api/*`), schémas Pydantic (`app/schemas/*`), modèles SQLAlchemy (`app/models/*`) et dépendances d’autorisation (`app/api/deps.py`).  
> **Statuts** : **Implémenté/fonctionnel (code)** = route et logique présentes ; **Implémenté, non vérifié** = présent mais non testé en E2E/production ; **Nécessaire, non développé** = absent. Aucun secret exposé.

## 1. Conventions globales
- **Base URL** : `/api` (préfixe applicatif). Auth : `Authorization: Bearer <access_token>` sauf endpoints publics indiqués.
- **Erreurs** (format observé) : `{"detail":"...","error":{"code":"..."}}` via gestion `APIError` ; validation FastAPI/Pydantic → `422`.
- **Rôles** (`UserRole`) : `CANDIDAT`, `RESPONSABLE_ACADEMIQUE`, `RESPONSABLE_ENTRETIEN`, `DIRECTION`, `ADMINISTRATEUR`.

## 2. Authentification (support)
| Méthode | Endpoint | Description | Request | Response (ex.) | Codes / erreurs | Accès | Statut |
|---|---|---|---|---|---|---|---|
| POST | `/api/auth/register` | Inscription publique candidat. | JSON `{nom,email,mot_de_passe,role?}` (`UserCreate`) | `201` `UserRead` `{id,nom,email,role,est_actif,date_creation}` | 409 email existant, 422 validation | Public (rôle forcé `CANDIDAT`) | Implémenté/fonctionnel (code) |
| POST | `/api/auth/login` | Connexion. | `LoginRequest` `{email,mot_de_passe}` | `TokenResponse` (tokens + user) | 401/403 selon auth | Public | Implémenté, non vérifié E2E |
| POST | `/api/auth/refresh` | Renouvellement token. | `{token}` | `TokenResponse` | 401 token invalide | Public (token refresh) | Implémenté, non vérifié E2E |
| GET | `/api/auth/me` | Utilisateur courant. | — | `UserRead` | 401/403 | Authentifié | Implémenté, non vérifié E2E |

## 3. Gestion des candidats / candidatures
> Le dépôt modélise principalement la **candidature** (dossier) liée à un candidat (`candidat_id`) et un parcours.

| Méthode | Endpoint | Description / objectif | Paramètres & Request | Response (ex.) | Codes / erreurs | Autorisations (code) | Statut |
|---|---|---|---|---|---|---|---|
| POST | `/api/candidatures` | Déposer une candidature sur un parcours. | JSON `{ "parcours_id": "<uuid>" }` | `201` `CandidatureRead` `{id,candidat_id,parcours{...},date_depot,statut,responsable_academique_id,decision}` | 403 rôle, 404 parcours, 422 | **CANDIDAT** uniquement | Implémenté/fonctionnel (code) |
| GET | `/api/candidatures` | Lister candidatures selon rôle (pagination/filtres). | Query `statut?`, `parcours_id?`, `page=1`, `limit=20` | `CandidatureListResponse` `{items,total,page,limit}` | 403 liste non accessible | **CANDIDAT** (ses dossiers), **RESPONSABLE_ACADEMIQUE** (assignés), **ADMINISTRATEUR** (tous). `RESPONSABLE_ENTRETIEN`/autres : refus liste globale (code) | Implémenté/fonctionnel (code) |
| GET | `/api/candidatures/{candidature_id}` | Consulter un dossier. | Path `candidature_id` | `CandidatureRead` | 403 accès refusé, 404 | Accès contrôlé par `can_access_candidature` : admin ; candidat propriétaire ; responsable académique assigné ; responsable entretien lié à un entretien du dossier | Implémenté/fonctionnel (code) |
| PATCH | `/api/candidatures/{candidature_id}/decision` | Décision académique (accepter/rejeter/réorienter). | JSON `{decision:"ACCEPTER|REJETER|REORIENTER", commentaire?, parcours_destination_id?}` | `CandidatureRead` | 400 (réorientation invalide), 403, 404, 409 si pas `EN_ATTENTE` | **RESPONSABLE_ACADEMIQUE** ou **ADMINISTRATEUR** (vérifié dans service) | Implémenté, non vérifié E2E |
| GET | `/api/candidatures/{candidature_id}/qcm` | Consulter QCM associé. | Path | `QCMRead` | 403, 404 | Même contrôle d’accès dossier | Implémenté, non vérifié E2E |
| POST | `/api/candidatures/{candidature_id}/qcm/submit` | Soumettre QCM (1 passage, score figé). | `QCMSubmit` `{score:0..100}` | `201` `QCMRead` | 403, 404, 409 déjà soumis | Accès dossier (candidat/acteurs autorisés) | Implémenté, non vérifié E2E |
| GET | `/api/candidatures/{candidature_id}/qcm/result` | Résultat QCM. | Path | `QCMResultRead` | 403, 404 | Accès dossier | Implémenté, non vérifié E2E |
| GET | `/api/candidatures/{candidature_id}/demandes-complement` | Lister demandes de complément. | Path | `[DemandeComplementRead]` | 403, 404 | Accès dossier | Implémenté, non vérifié E2E |
| POST | `/api/candidatures/{candidature_id}/demandes-complement` | Créer demande de complément. | `DemandeComplementCreate` `{contenu, informations_attendues?, type_document?}` | `201` `DemandeComplementRead` | 403, 404, 422 | Selon logique service entretien (acteurs habilités) | Implémenté, non vérifié E2E |
| GET | `/api/users/*` | Gestion comptes (CRUD admin partiel, pas de DELETE exposé). | Voir `app/api/users.py` | `UserRead`/liste | 401/403 | **ADMINISTRATEUR** (router dépend de `require_role(ADMINISTRATEUR)`) | Implémenté/fonctionnel (code) |
| — | API “candidat” dédiée (profil candidat séparé, listing public candidats, etc.) | Non exposée comme ressource distincte de `users/candidatures`. | — | — | — | — | **Nécessaire selon besoin métier, non développé** (hors existant) |

## 4. Gestion des conversations
| Méthode | Endpoint | Description / objectif | Paramètres & Request | Response (ex.) | Codes / erreurs | Autorisations (code) | Statut |
|---|---|---|---|---|---|---|---|
| POST | `/api/conversations` | Créer une conversation candidat/chatbot. | — (auth) | `201` `ConversationRead` `{id,candidat_id,created_at,updated_at}` | 403 rôle | **CANDIDAT** uniquement | Implémenté/fonctionnel (code) |
| GET | `/api/conversations/{conversation_id}` | Consulter conversation + messages. | Path | `ConversationDetailResponse` `{id,candidat_id,created_at,updated_at,messages:[{id,conversation_id,sender_id,contenu,est_assistant,created_at}]}` | 403, 404 | **Propriétaire candidat ou ADMINISTRATEUR** (`get_conversation_for_user`) | Implémenté/fonctionnel (code) |
| GET | `/api/conversations/{conversation_id}/messages` | Historique des messages. | Path | `[MessageRead]` | 403, 404 | Propriétaire candidat ou admin | Implémenté/fonctionnel (code) |
| POST | `/api/conversations/{conversation_id}/messages` | Envoyer un message ; génère réponse chatbot **si configuré**. | JSON `{ "contenu": "..." }` (1–5000) | `201` `MessageRead` (message envoyé) | 403, 404, 422, **503 `CHATBOT_NOT_CONFIGURED`** si chatbot non configuré | Propriétaire candidat ou admin (accès conversation) | **Implémenté (garde fonctionnelle)** ; réponse IA **non opérationnelle** sans config LLM |

**APIs manquantes (si requises)** : liste des conversations d’un candidat, clôture/suppression, endpoints temps réel/websocket — **non développées**.

## 5. Gestion des documents
| Méthode | Endpoint | Description / objectif | Paramètres & Request | Response (ex.) | Codes / erreurs | Autorisations (code) | Statut |
|---|---|---|---|---|---|---|---|
| POST | `/api/candidatures/{candidature_id}/documents` | Upload d’un document au dossier. | `multipart/form-data` champ `file` (`UploadFile`) | `201` `DocumentRead` `{id,candidature_id,nom,type,taille_octets,date_ajout}` | 400 (taille max, vide, extension non autorisée), 403, 404, 422 | Contrôle d’accès dossier (`can_access_candidature`) — candidats/acteurs autorisés sur le dossier | Implémenté/fonctionnel (code) |
| GET | `/api/candidatures/{candidature_id}/documents` | Lister documents du dossier. | Path | `[DocumentRead]` | 403, 404 | Contrôle d’accès dossier | Implémenté/fonctionnel (code) |
| GET | `/api/documents/{document_id}/download` | Téléchargement contrôlé (fichier). | Path | Fichier binaire (`FileResponse`, `media_type`, `filename`) | 403, 404 si métadonnée/fichier absent | Contrôle d’accès via dossier associé | Implémenté/fonctionnel (code) |
| — | Suppression/remplacement de document, scan antivirus, stockage objet (S3) | — | — | — | — | — | **Nécessaire selon exigences, non développé** |

**Exemple Request (upload)** : `POST /api/candidatures/{id}/documents` — `Content-Type: multipart/form-data`, `file=@releve.pdf` (extensions/taille bornées par config).

## 6. API IA pertinentes (existantes)
| Méthode | Endpoint | Description | Request | Response / comportement | Accès | Statut |
|---|---|---|---|---|---|---|
| POST | `/api/conversations/{id}/messages` | Point d’entrée chatbot (voir §4). | `{contenu}` | `201` message ou `503 CHATBOT_NOT_CONFIGURED` | Accès conversation | Garde implémentée ; IA non opérationnelle |
| POST | `/api/admin/rag/reindex` | Déclencher réindexation RAG. | — | `dict` (service `reindex()`) | **ADMINISTRATEUR** | Implémenté (dépend config/corpus) |
| GET | `/api/admin/rag/status` | Statut configuration RAG. | — | `dict` (`get_rag_status()`) | **ADMINISTRATEUR** | Implémenté |

## 7. Autres API existantes (hors périmètre principal demandé)
| Domaine | Endpoints (observés) | Accès (code) | Statut |
|---|---|---|---|
| Parcours | `GET /api/parcours`, `GET /api/parcours/{id}` | Public (pas de `get_current_user` sur routes) | Implémenté/fonctionnel (code) |
| Entretiens | `GET /api/entretiens`, `POST /api/candidatures/{id}/entretiens`, `PATCH /api/entretiens/{id}/approval` | Authentifié ; règles métier dans services | Implémenté, non vérifié E2E |
| Dashboard | `GET /api/dashboard/stats`, `GET /api/dashboard/export?format=` | Authentifié ; contenu selon rôle/service | Implémenté, non vérifié E2E |
| Santé | `GET /api/health` | Public | Implémenté/fonctionnel (vérifié) |