import sqlite3
import requests
import os
import time
from dotenv import load_dotenv

# Charge la clé API Last.fm depuis le .env
load_dotenv()
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

def get_artist_genres(artist_name):
    """Interroge Last.fm pour récupérer les genres (tags) d'un artiste"""
    if not LASTFM_API_KEY:
        return ""
    
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.getTopTags",
        "artist": artist_name,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=5).json()
        tags = response.get('toptags', {}).get('tag', [])
        # On récupère les 3 genres les plus populaires
        genre_list = [t['name'] for t in tags[:3]]
        return ", ".join(genre_list)
    except Exception:
        return ""

def update_genres_in_db():
    conn = sqlite3.connect('spotify_data.db')
    cursor = conn.cursor()

    # 1. Identifier les artistes uniques qui n'ont pas de genres renseignés
    # On cherche les lignes où artist_genres est vide ou NULL
    query_missing = """
        SELECT DISTINCT artist_name 
        FROM history 
        WHERE artist_genres IS NULL OR artist_genres = ''
    """
    cursor.execute(query_missing)
    artists_to_update = cursor.fetchall()

    if not artists_to_update:
        print("✅ Tous les artistes de la base ont déjà leurs genres renseignés !")
        conn.close()
        return

    print(f"🔍 {len(artists_to_update)} artistes trouvés avec des genres manquants.")
    print("🚀 Début de la mise à jour...")

    updated_count = 0
    for row in artists_to_update:
        # artist_name est le premier élément du tuple
        full_name = row[0]
        # On prend le premier artiste si c'est un feat (comme dans ton fetch_history.py)
        main_artist = full_name.split(',')[0].strip()
        
        genres = get_artist_genres(main_artist)
        
        if genres:
            # On met à jour TOUTES les lignes de cet artiste dans la base
            cursor.execute('''
                UPDATE history 
                SET artist_genres = ? 
                WHERE artist_name = ? AND (artist_genres IS NULL OR artist_genres = '')
            ''', (genres, full_name))
            
            updated_count += 1
            print(f"   ✅ {full_name} -> {genres}")
        else:
            print(f"   ⚠️ Aucun genre trouvé pour {full_name}")

        # Petite pause pour respecter les limites de l'API Last.fm
        time.sleep(0.2)

    conn.commit()
    conn.close()
    print(f"\n✨ Terminé ! {updated_count} artistes mis à jour avec succès.")

if __name__ == "__main__":
    update_genres_in_db()