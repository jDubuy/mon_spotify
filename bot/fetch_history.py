import sqlite3
import spotipy
import requests
import os
import time
import subprocess
import datetime
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

def get_spotify_client():
    # AJOUT DU SCOPE user-top-read
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope="user-read-recently-played user-top-read", 
        open_browser=False
    ))

def get_artist_genres(artist_name):
    """Récupère les genres sur Last.fm"""
    if not LASTFM_API_KEY: return ""
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {"method": "artist.getTopTags", "artist": artist_name, "api_key": LASTFM_API_KEY, "format": "json"}
    try:
        response = requests.get(url, params=params, timeout=5).json()
        tags = response.get('toptags', {}).get('tag', [])
        return ", ".join([t['name'] for t in tags[:3]])
    except: return ""

def fill_missing_genres():
    """Scanne la DB pour remplir les genres manquants"""
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT artist_name FROM artists WHERE artist_genres IS NULL OR artist_genres = ''")
    to_fix = cursor.fetchall()
    
    fixed_count = 0
    if to_fix:
        for row in to_fix:
            full_name = row[0]
            main_artist = full_name.split(',')[0].strip()
            genres = get_artist_genres(main_artist)
            if genres:
                cursor.execute("UPDATE artists SET artist_genres = ? WHERE artist_name = ?", (genres, full_name))
                fixed_count += 1
                time.sleep(0.2)
        conn.commit()
    conn.close()
    return fixed_count

def git_push_db():
    """Pousse la base de données sur GitHub"""
    try:
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if "spotify_data.db" in status:
            subprocess.run(["git", "add", "spotify_data.db"], check=True, timeout=30)
            maintenant = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Mise à jour DB (Synchro) : {maintenant}"
            subprocess.run(["git", "commit", "-m", message], check=True, timeout=30)
            subprocess.run(["git", "push"], check=True, timeout=60)
            return True
        return False
    except: return False

def get_recommendations(sp, limit=10):
    """Génère des recommandations basées sur les tops récents"""
    try:
        # 1. Graines : Top artistes récents
        top_artists = sp.current_user_top_artists(limit=5, time_range='short_term')
        seed_artists = [artist['id'] for artist in top_artists['items']]

        # Fallback si pas de top artistes : utiliser les derniers morceaux écoutés
        if not seed_artists:
            recent = sp.current_user_recently_played(limit=5)
            seed_tracks = [item['track']['id'] for item in recent['items']]
            if not seed_tracks: return []
            recs = sp.recommendations(seed_tracks=seed_tracks, limit=limit * 2)
        else:
            recs = sp.recommendations(seed_artists=seed_artists, limit=limit * 2)
        
        # 2. Filtrer pour exclure ce qui est déjà en DB
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
            if len(new_recs) >= limit: break
        return new_recs
    except Exception as e:
        print(f"Erreur Recommandations : {e}")
        return []

def save_to_db(tracks):
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    cursor = conn.cursor()
    ajouts = []
    for item in tracks['items']:
        track = item['track']
        try:
            # Architecture multi-tables
            artistes = [a['name'] for a in track.get('artists', [])]
            nom_complet = ", ".join(artistes)
            genres = get_artist_genres(artistes[0])
            album_name = track['album']['name']
            release_date = track['album']['release_date']
            pochette = track['album']['images'][0]['url'] if track['album']['images'] else ''

            cursor.execute('INSERT OR IGNORE INTO artists (artist_name, artist_genres) VALUES (?, ?)', (nom_complet, genres))
            cursor.execute('INSERT OR IGNORE INTO albums (album_name, artist_name, album_cover_url, release_date) VALUES (?, ?, ?, ?)', (album_name, nom_complet, pochette, release_date))
            cursor.execute('INSERT OR IGNORE INTO tracks (track_id, track_name, artist_name, album_name, duration_ms) VALUES (?, ?, ?, ?, ?)', (track['id'], track['name'], nom_complet, album_name, track['duration_ms']))
            cursor.execute('INSERT OR IGNORE INTO history (played_at, track_id) VALUES (?, ?)', (item['played_at'], track['id']))
            
            if cursor.rowcount == 1:
                ajouts.append(f"{nom_complet} - {track['name']}")
        except: continue
    conn.commit()
    conn.close()
    return ajouts

def main():
    try:
        sp = get_spotify_client()
        recent = sp.current_user_recently_played(limit=50)
        nouveaux = save_to_db(recent)
        fill_missing_genres()
        if nouveaux: git_push_db()
        return nouveaux
    except Exception as e:
        print(f"❌ Erreur main : {e}")
        return []