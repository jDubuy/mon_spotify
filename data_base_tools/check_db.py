import sqlite3
import pandas as pd

def check_database():
    conn = sqlite3.connect('spotify_data.db')
    
    # On demande la colonne 'popularity' au lieu de 'genres'
    query = "SELECT played_at, artist_name, track_name, popularity FROM history ORDER BY played_at DESC LIMIT 10"
    df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    if df.empty:
        print("La base de données est vide.")
    else:
        print("🔍 VOICI TES 10 DERNIÈRES ÉCOUTES EN BASE DE DONNÉES :\n")
        print(df.to_string(index=False))

if __name__ == "__main__":
    check_database()