import sqlite3

conn = sqlite3.connect('spotify_data.db')
cursor = conn.cursor()

try:
    # On ajoute la colonne pour stocker le lien de l'image
    cursor.execute("ALTER TABLE history ADD COLUMN album_cover_url TEXT DEFAULT ''")
    print("✅ Colonne 'album_cover_url' ajoutée avec succès !")
except sqlite3.OperationalError:
    print("ℹ️ La colonne existe déjà.")

conn.commit()
conn.close()