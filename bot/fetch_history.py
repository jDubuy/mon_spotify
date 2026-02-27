# bot/fetch_history.py
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from bot.services.lastfm import fetch_genres
from utils.database import get_db

load_dotenv()
logger = logging.getLogger(__name__)

def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-read-recently-played user-top-read",
        open_browser=False
    ))

def save_to_db(tracks):
    """Utilise le gestionnaire de contexte get_db pour sauvegarder les titres"""
    ajouts = []
    with get_db() as conn:
        cursor = conn.cursor()
        for item in tracks['items']:
            track = item['track']
            try:
                nom_complet = ", ".join([a['name'] for a in track['artists']])
                genres = fetch_genres(track['artists'][0]['name']) # Utilise le service Last.fm
                
                cursor.execute('INSERT OR IGNORE INTO artists VALUES (?, ?)', (nom_complet, genres))
                cursor.execute('INSERT OR IGNORE INTO albums VALUES (?, ?, ?, ?)', 
                               (track['album']['name'], nom_complet, track['album']['images'][0]['url'], track['album']['release_date']))
                cursor.execute('INSERT OR IGNORE INTO tracks VALUES (?, ?, ?, ?, ?)', 
                               (track['id'], track['name'], nom_complet, track['album']['name'], track['duration_ms']))
                cursor.execute('INSERT OR IGNORE INTO history VALUES (?, ?)', (item['played_at'], track['id']))
                
                if cursor.rowcount == 1:
                    ajouts.append(f"{nom_complet} - {track['name']}")
            except Exception as e:
                logger.error(f"Erreur d'insertion : {e}")
        conn.commit()
    return ajouts

def main():
    logger.info("Démarrage de la synchronisation...")
    sp = get_spotify_client()
    recent = sp.current_user_recently_played(limit=50)
    return save_to_db(recent)