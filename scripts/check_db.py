"""Script de verification de la connexion base de donnees (sans afficher de secrets)."""
import os
import sys

# S'assurer que le projet est dans le path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.db.session import _url_parts, database_url, engine


def main():
    parts = _url_parts(database_url)
    print(f"[DB cible] type={parts['type']} host={parts['host']} database={parts['database']}")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connexion base de donnees: OK")
        return 0
    except Exception as e:
        print(f"Connexion base de donnees: ECHEC ({type(e).__name__})")
        print("Verifiez DATABASE_URL/DATABASE_URL_DIRECT dans le .env du projet, reseau et SSL (sans exposer d'identifiants).")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
