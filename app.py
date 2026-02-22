import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ma Dataviz Spotify", page_icon="🎧", layout="wide")

st.title("🎧 Mon Dashboard Spotify : Analyse de mes habitudes")

@st.cache_data
def load_data():
    conn = sqlite3.connect('spotify_data.db')
    df = pd.read_sql_query("SELECT played_at, track_name, artist_name, duration_ms FROM history", conn)
    conn.close()
    
    if not df.empty:
        # Conversion du fuseau horaire pour avoir tes vraies heures locales
        df['played_at'] = pd.to_datetime(df['played_at']).dt.tz_convert('Europe/Paris')
        df['date'] = df['played_at'].dt.date
        df['hour'] = df['played_at'].dt.hour
        df['day_name'] = df['played_at'].dt.day_name()
    return df

df = load_data()

if df.empty:
    st.warning("Ta base de données est vide.")
else:
    # --- KPIs ---
    heures_total = df['duration_ms'].sum() / (1000 * 60 * 60)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🎵 Morceaux écoutés", len(df))
    col2.metric("🎤 Artistes différents", df['artist_name'].nunique())
    col3.metric("⏱️ Heures de musique", f"{heures_total:.1f} h")
    
    st.divider()

    # --- LIGNE 1 : Les Tops ---
    col_g, col_d = st.columns(2)
    
    with col_g:
        st.subheader("🏆 Mes Artistes en boucle")
        st.bar_chart(df['artist_name'].value_counts().head(7))
        
    with col_d:
        st.subheader("🔁 Mes Morceaux les plus saignés")
        st.bar_chart(df['track_name'].value_counts().head(7))

    st.divider()

    # --- LIGNE 2 : Les Habitudes temporelles ---
    st.subheader("🕒 Quand est-ce que j'écoute le plus de musique ?")
    col_g2, col_d2 = st.columns(2)
    
    with col_g2:
        st.markdown("**Par heure de la journée**")
        # On compte les écoutes par heure et on trie de 00h à 23h
        ecoutes_heure = df.groupby('hour').size()
        st.bar_chart(ecoutes_heure)
        
    with col_d2:
        st.markdown("**Par jour de la semaine**")
        # Ordre des jours pour que le graphique soit logique
        jours_ordre = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ecoutes_jour = df['day_name'].value_counts().reindex(jours_ordre).fillna(0)
        st.bar_chart(ecoutes_jour)