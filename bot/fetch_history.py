import sqlite3
import spotipy
import requests
import os
import logging
import sys
from pathlib import Path
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.lastfm import fetch_genres
from utils.database import get_db

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def get_spotify_client():
    """Initialise le client Spotify avec les bons scopes"""
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-read-recently-played user-top-read",
        open_browser=False
    ))

def get_recommendations(sp, limit=12):
    """Génère des suggestions basées sur tes tops récents"""
    try:
        # 1. Récupération des graines (Top artistes)
        top_artists = sp.current_user_top_artists(limit=5, time_range='short_term')
        seed_artists = [a['id'] for a in top_artists['items']]

        if not seed_artists:
            # Fallback sur les morceaux récents si pas de top artistes
            recent = sp.current_user_recently_played(limit=5)
            seed_tracks = [item['track']['id'] for item in recent['items']]
            if not seed_tracks: return []
            recs = sp.recommendations(seed_tracks=seed_tracks, limit=limit)
        else:
            recs = sp.recommendations(seed_artists=seed_artists, limit=limit)
        
        # 2. Filtrage des titres déjà connus en base pour ne proposer que de la nouveauté
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT track_id FROM tracks")
            known_ids = {row['track_id'] for row in cursor.fetchall()}

        new_recs = []
        for track in recs.get('tracks', []):
            if track['id'] not in known_ids:
                new_recs.append({
                    'name': track['name'],
                    'artist': ', '.join([a['name'] for a in track['artists']]),
                    'cover': track['album']['images'][0]['url'] if track['album']['images'] else '',
                    'url': track['external_urls']['spotify']
                })
        return new_recs[:limit]
    except Exception as e:
        logger.error(f"Erreur lors de la génération de recommandations : {e}")
        return []

def save_to_db(tracks):
    """Enregistre les morceaux dans la base de données"""
    with get_db() as conn:
        cursor = conn.cursor()
        for item in tracks.get('items', []):
            track = item['track']
            try:
                played_at = item['played_at']
                track_id = track['id']
                track_name = track['name']
                artist_name = ', '.join([a['name'] for a in track['artists']])
                duration_ms = track['duration_ms']
                album_name = track['album']['name']
                album_cover = track['album']['images'][0]['url'] if track['album']['images'] else ''
                
                # Récupérer les genres via Last.fm
                genres = fetch_genres(track['artists'][0]['name']) if track['artists'] else ''
                
                # Insérer l'artiste
                cursor.execute('INSERT OR IGNORE INTO artists VALUES (?, ?)', (artist_name, genres))
                
                # Insérer l'album
                cursor.execute('INSERT OR IGNORE INTO albums VALUES (?, ?, ?, ?)', 
                             (album_name, artist_name, album_cover, track['album']['release_date']))
                
                # Insérer le morceau
                cursor.execute('INSERT OR IGNORE INTO tracks VALUES (?, ?, ?, ?, ?)',
                             (track_id, track_name, artist_name, album_name, duration_ms))
                
                # Insérer dans l'historique
                cursor.execute('INSERT OR IGNORE INTO history VALUES (?, ?)', (played_at, track_id))
                
                logger.info(f"✅ {track_name} - {artist_name} ajouté")
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement de {track.get('name')}: {e}")
        
        conn.commit()

def main():
    """Orchestre la synchronisation complète"""
    logger.info("🎵 Démarrage de la synchronisation Spotify...")
    sp = get_spotify_client()
    
    # Récupérer les 50 derniers morceaux écoutés
    try:
        recent_tracks = sp.current_user_recently_played(limit=50)
        save_to_db(recent_tracks)
        logger.info(f"✅ Synchronisation complète ! {len(recent_tracks.get('items', []))} morceaux traités.")
        return recent_tracks.get('items', [])
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération : {e}")
        return []

if __name__ == "__main__":
    main()
