import sqlite3
conn = sqlite3.connect('spotify_data.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE history ADD COLUMN artist_genres TEXT DEFAULT ''")
    print("✅ Colonne 'artist_genres' prête !")
except:
    print("ℹ️ La colonne existe déjà.")
conn.commit()
conn.close()