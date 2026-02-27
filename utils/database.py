# utils/database.py
import sqlite3
from contextlib import contextmanager

DB_PATH = 'spotify_data.db'

@contextmanager
def get_db():
    """Gestionnaire de contexte pour assurer la fermeture propre de la DB"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_setting(key, default=None):
    """Récupère un réglage depuis la table settings"""
    with get_db() as conn:
        res = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return res['value'] if res else default

def save_setting(key, value):
    """Enregistre un réglage dans la table settings"""
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

def load_full_history():
    """Charge l'historique complet avec les jointures"""
    query = '''
        SELECT h.played_at, t.track_name, t.artist_name, t.duration_ms, 
               alb.album_cover_url, art.artist_genres, alb.album_name, alb.release_date
        FROM history h
        JOIN tracks t ON h.track_id = t.track_id
        JOIN artists art ON t.artist_name = art.artist_name
        JOIN albums alb ON t.album_name = alb.album_name AND t.artist_name = alb.artist_name
    '''
    with get_db() as conn:
        import pandas as pd
        return pd.read_sql_query(query, conn)