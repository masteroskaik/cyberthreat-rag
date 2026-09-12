"""
Gestion de la connexion PostgreSQL (Neon) pour le projet CyberThreat RAG.
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL, check_required_env


@contextmanager
def get_connection():
    """
    Fournit une connexion PostgreSQL dans un context manager.

    Usage :
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")
    """
    check_required_env("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema():
    """Exécute le fichier schema.sql pour créer les tables si elles n'existent pas."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)

    print("Schéma initialisé avec succès.")


if __name__ == "__main__":
    init_schema()
