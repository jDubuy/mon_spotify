import sqlite3
import pandas as pd

def check_database():
    conn = sqlite3.connect('spotify_data.db')
    
    # Jointure avec la table tracks pour récupérer les infos des morceaux
    query = """
    SELECT h.played_at, t.track_name, t.artist_name, t.duration_ms 
    FROM history h
    JOIN tracks t ON h.track_id = t.track_id
    ORDER BY h.played_at DESC 
    LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    if df.empty:
        print("La base de données est vide.")
    else:
        print("🔍 VOICI TES 10 DERNIÈRES ÉCOUTES EN BASE DE DONNÉES :\n")
        print(df.to_string(index=False))

if __name__ == "__main__":
    check_database()