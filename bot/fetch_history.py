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
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played", open_browser=False))

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
    cursor.execute("SELECT DISTINCT artist_name FROM history WHERE artist_genres IS NULL OR artist_genres = ''")
    to_fix = cursor.fetchall()
    
    fixed_count = 0
    if to_fix:
        for row in to_fix:
            full_name = row[0]
            main_artist = full_name.split(',')[0].strip()
            genres = get_artist_genres(main_artist)
            if genres:
                cursor.execute("UPDATE history SET artist_genres = ? WHERE artist_name = ? AND (artist_genres = '' OR artist_genres IS NULL)", (genres, full_name))
                fixed_count += 1
                time.sleep(0.2)
        conn.commit()
    conn.close()
    return fixed_count

def git_push_db():
    """Pousse la base de données sur GitHub"""
    try:
        # On vérifie s'il y a des changements avant de push
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if "spotify_data.db" in status:
            subprocess.run(["git", "add", "spotify_data.db"], check=True, timeout=30)
            maintenant = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Mise à jour DB (Synchro) : {maintenant}"
            subprocess.run(["git", "commit", "-m", message], check=True, timeout=30)
            subprocess.run(["git", "push"], check=True, timeout=60)
            print("🚀 GitHub : Base de données synchronisée !")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Erreur Git : {e}")
        return False

def save_to_db(tracks):
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    cursor = conn.cursor()
    ajouts = []
    for item in tracks['items']:
        track = item['track']
        try:
            artistes = [a['name'] for a in track.get('artists', [])]
            nom_complet = ", ".join(artistes)
            genres = get_artist_genres(artistes[0])
            pochette = track['album']['images'][0]['url'] if track['album']['images'] else ''
            
            cursor.execute('''
                INSERT OR IGNORE INTO history 
                (played_at, track_id, track_name, artist_name, duration_ms, album_cover_url, artist_genres, album_name, release_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['played_at'], track.get('id', ''), track.get('name', 'Inconnu'), nom_complet, track.get('duration_ms', 0), pochette, genres, track['album']['name'], track['album']['release_date']))
            
            if cursor.rowcount == 1:
                ajouts.append(f"{nom_complet} - {track.get('name')}")
        except: continue
    conn.commit()
    conn.close()
    return ajouts

def main():
    """Fonction principale appelée par le Bot ou par l'App Streamlit"""
    try:
        sp = get_spotify_client()
        recent = sp.current_user_recently_played(limit=50)
        nouveaux = save_to_db(recent)
        
        # On nettoie les genres
        nb_fixes = fill_missing_genres()
        
        # Si quelque chose a changé (nouveaux sons ou genres réparés), on push sur Git
        if nouveaux or nb_fixes > 0:
            git_push_db()
            
        return nouveaux
    except Exception as e:
        print(f"❌ Erreur main : {e}")
        return []

if __name__ == "__main__":
    main()