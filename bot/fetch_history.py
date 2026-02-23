import sqlite3
import spotipy
import requests
import os
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played", open_browser=False))

def get_artist_genres(artist_name):
    if not LASTFM_API_KEY: return ""
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {"method": "artist.getTopTags", "artist": artist_name, "api_key": LASTFM_API_KEY, "format": "json"}
    try:
        response = requests.get(url, params=params, timeout=5).json()
        tags = response.get('toptags', {}).get('tag', [])
        return ", ".join([t['name'] for t in tags[:3]])
    except: return ""

def save_to_db(tracks):
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    cursor = conn.cursor()
    ajouts = []
    for item in tracks['items']:
        track = item['track']
        try:
            artistes = [a['name'] for a in track.get('artists', [])]
            nom_principal = artistes[0]
            nom_complet = ", ".join(artistes)
            genres = get_artist_genres(nom_principal)
            pochette = track['album']['images'][0]['url'] if track['album']['images'] else ''
            
            # --- NOUVELLES INFOS ---
            album_name = track['album']['name']
            release_date = track['album']['release_date']

            cursor.execute('''
                INSERT OR IGNORE INTO history 
                (played_at, track_id, track_name, artist_name, duration_ms, album_cover_url, artist_genres, album_name, release_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['played_at'], track.get('id', ''), track.get('name', 'Inconnu'), nom_complet, track.get('duration_ms', 0), pochette, genres, album_name, release_date))
            
            if cursor.rowcount == 1:
                ajouts.append(f"{nom_complet} - {track.get('name')}")
        except Exception as e:
            print(f"Erreur : {e}")
    conn.commit()
    conn.close()
    return ajouts

def main():
    try:
        sp = get_spotify_client()
        recent = sp.current_user_recently_played(limit=50)
        return save_to_db(recent)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return []

if __name__ == "__main__":
    main()