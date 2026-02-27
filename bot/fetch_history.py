import sqlite3
import spotipy
import requests
import os
import logging
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

def get_spotify_client():
    """Initialise le client Spotify avec les bons scopes"""
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-read-recently-played user-top-read",
        open_browser=False
    ))

def get_artist_genres(artist_name):
    """Récupère les genres via l'API Last.fm"""
    if not LASTFM_API_KEY: return ""
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {"method": "artist.getTopTags", "artist": artist_name, "api_key": LASTFM_API_KEY, "format": "json"}
    try:
        response = requests.get(url, params=params, timeout=5).json()
        tags = response.get('toptags', {}).get('tag', [])
        return ", ".join([t['name'] for t in tags[:3]])
    except Exception as e:
        logger.warning(f"Impossible de récupérer les genres pour {artist_name}: {e}")
        return ""

def get_recommendations(sp, limit=12):
    """Génère des suggestions basées sur tes tops"""
    try:
        top_artists = sp.current_user_top_artists(limit=5, time_range='short_term')
        seed_artists = [a['id'] for a in top_artists['items']]

        if not seed_artists:
            recent = sp.current_user_recently_played(limit=5)
            seed_tracks = [item['track']['id'] for item in recent['items']]
            recs = sp.recommendations(seed_tracks=seed_tracks, limit=limit)
        else:
            recs = sp.recommendations(seed_artists=seed_artists, limit=limit)
        
        # Filtrage
        conn = sqlite3.connect('spotify_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT track_id FROM tracks")
        known_ids = {row[0] for row in cursor.fetchall()}
        conn.close()

        new_recs = []
        for track in recs.get('tracks', []):
            if track['id'] not in known_ids:
                new_recs.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'cover': track['album']['images'][0]['url'] if track['album']['images'] else '',
                    'url': track['external_urls']['spotify']
                })
        return new_recs
    except Exception as e:
        logger.error(f"Erreur lors des recommandations: {e}")
        return []

def save_to_db(tracks):
    """Sauvegarde les lectures dans la base multi-tables"""
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    cursor = conn.cursor()
    ajouts = []
    
    for item in tracks['items']:
        track = item['track']
        try:
            nom_complet = ", ".join([a['name'] for a in track['artists']])
            genres = get_artist_genres(track['artists'][0]['name'])
            
            cursor.execute('INSERT OR IGNORE INTO artists VALUES (?, ?)', (nom_complet, genres))
            cursor.execute('INSERT OR IGNORE INTO albums VALUES (?, ?, ?, ?)', 
                           (track['album']['name'], nom_complet, track['album']['images'][0]['url'], track['album']['release_date']))
            cursor.execute('INSERT OR IGNORE INTO tracks VALUES (?, ?, ?, ?, ?)', 
                           (track['id'], track['name'], nom_complet, track['album']['name'], track['duration_ms']))
            cursor.execute('INSERT OR IGNORE INTO history VALUES (?, ?)', (item['played_at'], track['id']))
            
            if cursor.rowcount == 1:
                ajouts.append(f"{nom_complet} - {track['name']}")
        except Exception as e:
            logger.error(f"Erreur d'insertion pour {track.get('name')}: {e}")
            
    conn.commit()
    conn.close()
    return ajouts

def main():
    logger.info("Démarrage de la synchronisation...")
    try:
        sp = get_spotify_client()
        recent = sp.current_user_recently_played(limit=50)
        nouveaux = save_to_db(recent)
        logger.info(f"Synchro terminée. {len(nouveaux)} nouveaux titres ajoutés.")
        return nouveaux
    except Exception as e:
        logger.error(f"Échec de la synchronisation : {e}")
        return []