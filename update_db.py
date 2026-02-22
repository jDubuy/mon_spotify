import sqlite3

conn = sqlite3.connect('spotify_data.db')
cursor = conn.cursor()

try:
    # On ajoute une colonne "genres" à la table "history"
    cursor.execute("ALTER TABLE history ADD COLUMN genres TEXT DEFAULT ''")
    print("✅ Colonne 'genres' ajoutée avec succès à ta base de données !")
except sqlite3.OperationalError:
    print("ℹ️ La colonne 'genres' existe déjà.")

conn.commit()
conn.close()