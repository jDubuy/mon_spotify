import sqlite3

def migrate():
    conn = sqlite3.connect('spotify_data.db')
    cursor = conn.cursor()

    # 1. Création des nouvelles tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            artist_name TEXT PRIMARY KEY,
            artist_genres TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS albums (
            album_name TEXT,
            artist_name TEXT,
            album_cover_url TEXT,
            release_date TEXT,
            PRIMARY KEY (album_name, artist_name)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            track_id TEXT PRIMARY KEY,
            track_name TEXT,
            artist_name TEXT,
            album_name TEXT,
            duration_ms INTEGER
        )
    ''')

    # On renomme l'ancienne table history pour la migrer
    cursor.execute('ALTER TABLE history RENAME TO history_old')

    # Nouvelle table history simplifiée
    cursor.execute('''
        CREATE TABLE history (
            played_at TEXT PRIMARY KEY,
            track_id TEXT,
            FOREIGN KEY (track_id) REFERENCES tracks (track_id)
        )
    ''')

    # 2. Migration des données
    print("🚚 Migration des artistes...")
    cursor.execute('INSERT OR IGNORE INTO artists (artist_name, artist_genres) SELECT DISTINCT artist_name, artist_genres FROM history_old')

    print("🚚 Migration des albums...")
    cursor.execute('INSERT OR IGNORE INTO albums (album_name, artist_name, album_cover_url, release_date) SELECT DISTINCT album_name, artist_name, album_cover_url, release_date FROM history_old')

    print("🚚 Migration des morceaux...")
    cursor.execute('INSERT OR IGNORE INTO tracks (track_id, track_name, artist_name, album_name, duration_ms) SELECT DISTINCT track_id, track_name, artist_name, album_name, duration_ms FROM history_old')

    print("🚚 Migration de l'historique...")
    cursor.execute('INSERT OR IGNORE INTO history (played_at, track_id) SELECT played_at, track_id FROM history_old')

    # 3. Nettoyage (Optionnel : supprimer l'ancienne table après vérification)
    # cursor.execute('DROP TABLE history_old')

    conn.commit()
    conn.close()
    print("✅ Migration terminée avec succès !")

if __name__ == "__main__":
    migrate()