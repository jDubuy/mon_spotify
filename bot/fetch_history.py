import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played"))

def save_to_db(tracks):
    conn = sqlite3.connect('spotify_data.db')
    cursor = conn.cursor()
    compteur_ajouts = 0

    for item in tracks['items']:
        track = item['track']
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO history (played_at, track_id, track_name, artist_name, duration_ms)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item['played_at'], 
                track.get('id', ''), 
                track.get('name', 'Inconnu'), 
                track['artists'][0].get('name', 'Inconnu') if track.get('artists') else 'Inconnu',
                track.get('duration_ms', 0)
            ))
            
            if cursor.rowcount == 1:
                compteur_ajouts += 1
                
        except sqlite3.Error:
            pass

    conn.commit()
    conn.close()
    print(f"✅ {compteur_ajouts} nouveaux morceaux ajoutés (Synchronisation parfaite) !")

def main():
    try:
        sp = get_spotify_client()
        recent_tracks = sp.current_user_recently_played(limit=50)
        save_to_db(recent_tracks)
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")

if __name__ == "__main__":
    main()