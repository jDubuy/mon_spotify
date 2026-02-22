import sqlite3

conn = sqlite3.connect('spotify_data.db')
cursor = conn.cursor()

try:
    # On ajoute la colonne pour la note de 0 à 100
    cursor.execute("ALTER TABLE history ADD COLUMN popularity INTEGER DEFAULT 0")
    print("✅ Colonne 'popularity' ajoutée à ta base de données !")
except sqlite3.OperationalError:
    print("ℹ️ La colonne existe déjà.")

conn.commit()
conn.close()