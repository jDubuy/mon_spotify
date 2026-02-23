import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from bot import fetch_history #

# Configuration de la page
st.set_page_config(page_title="Spotify Stats", page_icon="🟢", layout="wide")

# --- STYLE CSS (Look Spotify) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #1DB954 !important; }
    div.stButton > button {
        background-color: #1DB954; color: white;
        border-radius: 500px; border: none;
        font-weight: bold; width: 100%;
    }
    [data-testid="stMetricValue"] { color: #1DB954 !important; }
    .profile-img {
        border-radius: 50%;
        width: 150px;
        border: 3px solid #1DB954;
        display: block; margin-left: auto; margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DE DONNÉES ---

@st.cache_data
def load_user_profile():
    try:
        sp = fetch_history.get_spotify_client()
        return sp.current_user()
    except:
        return None

@st.cache_data
def load_data():
    conn = sqlite3.connect('spotify_data.db')
    df = pd.read_sql_query("SELECT played_at, track_name, artist_name, duration_ms FROM history", conn)
    conn.close()
    if not df.empty:
        df['played_at'] = pd.to_datetime(df['played_at'])
        if df['played_at'].dt.tz is None:
            df['played_at'] = df['played_at'].dt.tz_localize('UTC')
        df['played_at'] = df['played_at'].dt.tz_convert('Europe/Paris')
        df['hour'] = df['played_at'].dt.hour
    return df

# --- BARRE LATÉRALE ---
user = load_user_profile()
df_raw = load_data()

with st.sidebar:
    if user:
        st.markdown(f"<h2 style='text-align: center;'>Salut, {user['display_name']} !</h2>", unsafe_allow_html=True)
        if user['images']:
            st.markdown(f"<img src='{user['images'][0]['url']}' class='profile-img'>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("⏳ Période d'analyse")
    filtre_temps = st.selectbox(
        "Choisir une plage :",
        options=["12 dernières heures", "3 derniers jours", "7 derniers jours", "1 mois", "6 mois", "1 an", "Depuis le début"],
        index=2
    )
    
    st.divider()
    if st.button('📡 Synchro API'):
        with st.spinner('Récupération...'):
            fetch_history.main() #
            st.cache_data.clear()
            st.rerun()
    if st.button('🔄 Refresh Page'):
        st.cache_data.clear()
        st.rerun()

# --- FILTRAGE ---
if not df_raw.empty:
    maintenant = pd.Timestamp.now(tz='Europe/Paris')
    if filtre_temps == "12 dernières heures": date_debut = maintenant - timedelta(hours=12)
    elif filtre_temps == "3 derniers jours": date_debut = maintenant - timedelta(days=3)
    elif filtre_temps == "7 derniers jours": date_debut = maintenant - timedelta(days=7)
    elif filtre_temps == "1 mois": date_debut = maintenant - timedelta(days=30)
    elif filtre_temps == "6 mois": date_debut = maintenant - timedelta(days=180)
    elif filtre_temps == "1 an": date_debut = maintenant - timedelta(days=365)
    else: date_debut = df_raw['played_at'].min()
    df = df_raw[df_raw['played_at'] >= date_debut].copy()
else:
    df = df_raw

# --- CORPS DU DASHBOARD ---
st.title("🟢 Mon Dashboard Spotify")

if df.empty:
    st.info(f"Aucune écoute pour la période : {filtre_temps}.")
else:
    # KPIs
    heures_total = df['duration_ms'].sum() / (1000 * 60 * 60)
    c1, c2, c3 = st.columns(3)
    c1.metric("🎵 Titres", len(df))
    c2.metric("🎤 Artistes", df['artist_name'].nunique())
    c3.metric("⏱️ Heures", f"{heures_total:.1f}")

    st.divider()

    # --- LIGNE 1 : LES TOPS (CORRIGÉ AVEC 01, 02...) ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"🏆 Tops Artistes ({filtre_temps})")
        top_artists = df['artist_name'].value_counts().head(10)
        # On utilise :02 pour transformer "1" en "01", ce qui force le bon tri
        top_artists.index = [f"{i+1:02}. {name}" for i, name in enumerate(top_artists.index)]
        st.bar_chart(top_artists, color="#1DB954")
        
    with col2:
        st.subheader(f"🔁 Tops Morceaux ({filtre_temps})")
        top_tracks = df['track_name'].value_counts().head(10)
        top_tracks.index = [f"{i+1:02}. {name}" for i, name in enumerate(top_tracks.index)]
        st.bar_chart(top_tracks, color="#1DB954")

    st.divider()

    # --- LIGNE 2 : LES HABITUDES ---
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🕒 Activité par Heure")
        st.bar_chart(df.groupby('hour').size(), color="#1DB954")
        
    with col4:
        st.subheader("📅 Activité par Jour")
        jours_traduction = {
            'Monday': '1. Lundi', 'Tuesday': '2. Mardi', 'Wednesday': '3. Mercredi',
            'Thursday': '4. Jeudi', 'Friday': '5. Vendredi', 'Saturday': '6. Samedi', 'Sunday': '7. Dimanche'
        }
        df['day_name_sort'] = df['played_at'].dt.day_name().map(jours_traduction)
        ordre_jours = ['1. Lundi', '2. Mardi', '3. Mercredi', '4. Jeudi', '5. Vendredi', '6. Samedi', '7. Dimanche']
        ecoutes_jour = df['day_name_sort'].value_counts().reindex(ordre_jours).fillna(0)
        st.bar_chart(ecoutes_jour, color="#1DB954")

    # --- SECTION : HISTORIQUE DÉTAILLÉ ---
    st.divider()
    st.subheader("📜 Historique de la période")
    nb_sons = st.selectbox("Afficher :", options=[5, 10, 25, 50, 100, "Tout"], index=1)
    limite = len(df) if nb_sons == "Tout" else nb_sons
    history_display = df[['played_at', 'track_name', 'artist_name']].sort_values('played_at', ascending=False).head(limite).copy()
    history_display['Date'] = history_display['played_at'].dt.strftime('%d/%m/%Y %H:%M')
    st.dataframe(history_display[['Date', 'track_name', 'artist_name']], use_container_width=True, hide_index=True)