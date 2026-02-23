import sqlite3
conn = sqlite3.connect('spotify_data.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE history ADD COLUMN album_name TEXT DEFAULT ''")
    cursor.execute("ALTER TABLE history ADD COLUMN release_date TEXT DEFAULT ''")
    print("✅ Colonnes Album et Date de sortie ajoutées !")
except:
    print("ℹ️ Les colonnes existent déjà.")
conn.commit()
conn.close()