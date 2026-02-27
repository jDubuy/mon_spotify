import sqlite3
from contextlib import contextmanager

DB_PATH = 'spotify_data.db'

@contextmanager
def get_db():
    """Gestionnaire de contexte pour assurer la fermeture propre de la DB"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialise les tables si elles n'existent pas"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Ici, place tes requêtes CREATE TABLE de ton script de migration
        conn.commit()