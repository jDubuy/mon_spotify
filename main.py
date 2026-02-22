import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Charge les identifiants depuis le fichier .env
load_dotenv()

# Définir les permissions dont on a besoin (lire tes tops et ton historique)
SCOPE = "user-top-read user-read-recently-played"

def get_spotify_client():
    # Création du système d'authentification
    auth_manager = SpotifyOAuth(scope=SCOPE)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

def main():
    sp = get_spotify_client()
    
    print("Connexion réussie ! Récupération des données...\n")
    
    # Récupère les 10 artistes les plus écoutés sur le court terme (environ 4 semaines)
    top_artists = sp.current_user_top_artists(limit=10, time_range='short_term')
    
    print("🏆 TES 10 ARTISTES LES PLUS ÉCOUTÉS CE MOIS-CI :")
    for index, artist in enumerate(top_artists['items']):
        print(f"{index + 1}. {artist['name']} (Genres : {', '.join(artist['genres'][:2])})")

if __name__ == "__main__":
    main()