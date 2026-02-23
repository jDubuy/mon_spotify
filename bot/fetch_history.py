import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Charge les variables d'environnement (.env)
load_dotenv()

def get_spotify_client():
    """Crée et retourne le client Spotify avec les permissions nécessaires"""
    # Utilisation du scope pour lire l'historique récent
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played"))

def save_to_db(tracks):
    """Sauvegarde les morceaux dans la base SQLite et retourne la liste des nouveaux ajouts"""
    # Connexion à la base de données située à la racine du projet
    conn = sqlite3.connect('spotify_data.db')
    cursor = conn.cursor()
    
    compteur_ajouts = 0
    morceaux_ajoutes = [] # Liste pour stocker le nom des nouveaux morceaux détectés

    for item in tracks['items']:
        track = item['track']
        
        try:
            # --- GESTION DES FEATS ---
            # On crée une liste de tous les artistes présents sur le morceau
            noms_artistes = [artist['name'] for artist in track.get('artists', [])]
            # On les regroupe dans une seule chaîne de caractères séparée par des virgules
            artist_name = ", ".join(noms_artistes) if noms_artistes else 'Inconnu'
            
            played_at = item['played_at']
            track_id = track.get('id', '')
            track_name = track.get('name', 'Inconnu')
            duration_ms = track.get('duration_ms', 0)

            # Insertion dans la table 'history'
            # INSERT OR IGNORE ignore l'insertion si la date 'played_at' existe déjà (clé primaire)
            cursor.execute('''
                INSERT OR IGNORE INTO history (played_at, track_id, track_name, artist_name, duration_ms)
                VALUES (?, ?, ?, ?, ?)
            ''', (played_at, track_id, track_name, artist_name, duration_ms))
            
            # Si le curseur indique qu'une ligne a été modifiée, c'est un nouveau morceau
            if cursor.rowcount == 1:
                compteur_ajouts += 1
                morceaux_ajoutes.append(f"{artist_name} - {track_name}")
                
        except sqlite3.Error:
            pass
        except Exception:
            pass

    conn.commit()
    conn.close()
    
    return morceaux_ajoutes # Retourne la liste à auto_fetch.py ou app.py

def main():
    """Fonction principale de récupération"""
    try:
        sp = get_spotify_client()
        # Récupération des 50 dernières écoutes via l'API Spotify
        recent_tracks = sp.current_user_recently_played(limit=50)
        
        # Sauvegarde et récupération de la liste des nouveautés
        return save_to_db(recent_tracks)
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération Spotify : {e}")
        return []

if __name__ == "__main__":
    # Test rapide si lancé manuellement
    resultat = main()
    if resultat:
        print(f"✅ Succès : {len(resultat)} nouveaux morceaux ajoutés.")
    else:
        print("ℹ️ Aucun nouveau morceau à ajouter.")