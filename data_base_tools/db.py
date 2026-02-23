import sqlite3

def init_db():
    # Crée un fichier 'spotify_data.db' (s'il n'existe pas) et s'y connecte
    conn = sqlite3.connect('spotify_data.db')
    cursor = conn.cursor()

    # Création d'une table simple pour stocker l'historique
    # On utilise 'played_at' comme clé primaire pour ne pas enregistrer de doublons
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            played_at TEXT PRIMARY KEY,
            track_id TEXT,
            track_name TEXT,
            artist_name TEXT,
            duration_ms INTEGER,
            album_cover_url TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de données 'spotify_data.db' prête !")

if __name__ == "__main__":
    init_db()