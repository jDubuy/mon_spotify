import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bot import fetch_history

# Configuration
load_dotenv()
st.set_page_config(page_title="Spotify Dashboard Pro", page_icon="🟢", layout="wide")

# --- FONCTIONS DE DONNÉES ---
@st.cache_data
def load_data():
    """Charge les données avec sécurité timeout"""
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    try:
        df = pd.read_sql_query("SELECT * FROM history", conn)
    except:
        df = pd.read_sql_query("SELECT played_at, track_name, artist_name, duration_ms, album_cover_url FROM history", conn)
    conn.close()
    if not df.empty:
        df['played_at'] = pd.to_datetime(df['played_at']).dt.tz_convert('Europe/Paris')
    return df

def get_artist_bio(artist_name):
    """Récupère la bio Last.fm"""
    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key: return None
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {"method": "artist.getInfo", "artist": artist_name, "api_key": api_key, "format": "json", "lang": "fr"}
    try:
        res = requests.get(url, params=params, timeout=5).json()
        return res.get('artist')
    except: return None

@st.dialog("Fiche de l'Artiste")
def show_artist_card(artist_name, df_full):
    """Mini-page pop-up pour l'artiste"""
    with st.spinner("Chargement de la bio..."):
        bio = get_artist_bio(artist_name)
    if bio:
        artist_rows = df_full[df_full['artist_name'].str.contains(artist_name, na=False)]
        img_path = artist_rows.iloc[0]['album_cover_url'] if not artist_rows.empty else ""
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(img_path if img_path else "https://www.scdn.co/scannables/svg/only-logo/255/white", width="stretch")
            st.metric("Écoutes", len(artist_rows))
        with col2:
            st.subheader(bio['name'])
            st.write(bio.get('bio', {}).get('summary', "").split('<a href')[0])
    else: st.error("Infos indisponibles.")

# --- CHARGEMENT ---
df_raw = load_data()

# --- STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    h1, h2, h3 { color: #1DB954 !important; font-family: 'Circular', sans-serif; }
    
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;
        margin-bottom: 10px; border-left: 5px solid #1DB954;
    }

    /* Bouton Artiste : Look lien Spotify */
    .artist-link-clean button {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        color: #1DB954 !important;
        text-align: left !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        box-shadow: none !important;
    }
    .artist-link-clean button:hover {
        color: #1ed760 !important;
        text-decoration: underline !important;
    }

    .track-card { 
        background: rgba(255,255,255,0.02); padding: 20px; 
        border-radius: 15px; margin-bottom: 15px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .meta-small { font-size: 0.85rem; color: #707070; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.title("🟢 Spotify Menu")
    if st.button('📡 Synchro Spotify'):
        fetch_history.main()
        st.cache_data.clear()
        st.rerun()
    filtre = st.selectbox("Période :", ["12h", "3 jours", "7 jours", "1 mois", "Tout"], index=2)

if not df_raw.empty:
    # --- LOGIQUE TEMPORELLE ---
    maintenant = pd.Timestamp.now(tz='Europe/Paris')
    dates_map = {"12h": maintenant - timedelta(hours=12), "3 jours": maintenant - timedelta(days=3), "7 jours": maintenant - timedelta(days=7), "1 mois": maintenant - timedelta(days=30), "Tout": df_raw['played_at'].min()}
    df = df_raw[df_raw['played_at'] >= dates_map[filtre]].copy()

    # --- DURÉE MOYENNE ---
    avg_ms = df['duration_ms'].mean() if not df.empty else 0
    avg_min, avg_sec = int(avg_ms // 60000), int((avg_ms % 60000) // 1000)

    # --- LAYOUT PRINCIPAL ---
    st.title("📊 Spotify Dashboard Pro")
    col_kpi, col_graphs = st.columns([1, 3], gap="large")

    with col_kpi:
        # Sélection par défaut : le dernier son écouté
        img_opts = df_raw[['track_name', 'album_cover_url', 'played_at']].sort_values('played_at', ascending=False).dropna()
        options_list = img_opts['track_name'].unique().tolist()
        choice = st.selectbox("Dernier écouté :", options_list, index=0)
        url = img_opts[img_opts['track_name'] == choice]['album_cover_url'].values[0]
        st.image(url if url else "https://www.scdn.co/scannables/svg/only-logo/255/white", width="stretch")
        
        st.divider()
        st.subheader("📈 Stats")
        st.metric("🎵 Titres", len(df))
        st.metric("🎤 Artistes", df['artist_name'].nunique())
        st.metric("⏱️ Heures Total", f"{df['duration_ms'].sum()/(3600000):.1f}")
        st.metric("⏳ Durée Moyenne", f"{avg_min}:{avg_sec:02d}")

    with col_graphs:
        # Tops Artistes et Titres
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏆 Top Artistes")
            top_a = df.groupby('artist_name').agg({'played_at': 'count', 'album_cover_url': 'first'}).reset_index().rename(columns={'played_at': 'Écoutes'}).sort_values('Écoutes', ascending=True).tail(8)
            fig_a = px.bar(top_a, y='artist_name', x='Écoutes', orientation='h', color_discrete_sequence=['#1DB954'], custom_data=['album_cover_url'])
            fig_a.update_traces(hovertemplate="<b>%{y}</b><br>Écoutes: %{x}<br><img src='%{customdata[0]}' width='100'>")
            fig_a.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=320, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_a, width="stretch")
        with c2:
            st.subheader("🔁 Top Titres")
            top_t = df.groupby('track_name').agg({'played_at': 'count', 'artist_name': 'first', 'album_cover_url': 'first'}).reset_index().rename(columns={'played_at': 'Écoutes'}).sort_values('Écoutes', ascending=True).tail(8)
            fig_t = px.bar(top_t, y='track_name', x='Écoutes', orientation='h', color_discrete_sequence=['#1DB954'], custom_data=['artist_name', 'album_cover_url'])
            fig_t.update_traces(hovertemplate="<b>%{y}</b><br>Écoutes: %{x}<br><img src='%{customdata[1]}' width='100'>")
            fig_t.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=320, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_t, width="stretch")

        # --- NOUVEAU : GRAPH DES GENRES (Réintégré) ---
        st.divider()
        st.subheader("🎸 Genres les plus écoutés")
        all_genres = []
        if 'artist_genres' in df.columns:
            for g in df['artist_genres'].dropna():
                if g: all_genres.extend([x.strip().capitalize() for x in g.split(',')])
        
        if all_genres:
            genre_counts = pd.Series(all_genres).value_counts().head(10).reset_index()
            genre_counts.columns = ['Genre', 'Count']
            fig_g = px.bar(genre_counts, x='Count', y='Genre', orientation='h', color_discrete_sequence=['#1DB954'])
            fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=350, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_g, width="stretch")
        else:
            st.info("Synchronise tes données pour voir tes genres préférés !")

    # --- HISTORIQUE DÉTAILLÉ (BIG COVERS) ---
    st.divider()
    st.subheader("📜 Historique Récent")
    recent = df.sort_values('played_at', ascending=False).head(15)
    
    for _, row in recent.iterrows():
        with st.container():
            st.markdown('<div class="track-card">', unsafe_allow_html=True)
            col_img, col_info = st.columns([1.5, 8.5])
            
            with col_img:
                img_url = row.get('album_cover_url', '')
                st.image(img_url if img_url else "https://www.scdn.co/scannables/svg/only-logo/255/white", width=100)
            
            with col_info:
                st.markdown(f"<h3 style='margin:0; font-size:1.5rem;'>{row['track_name']}</h3>", unsafe_allow_html=True)
                
                nom_art = row['artist_name'].split(',')[0]
                st.markdown('<div class="artist-link-clean">', unsafe_allow_html=True)
                if st.button(nom_art, key=f"link_{row['played_at']}"):
                    show_artist_card(nom_art, df_raw)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Formatage durée m:ss pour chaque ligne
                d = row.get('duration_ms', 0)
                st.markdown(f"<div class='meta-small'>💿 {row.get('album_name','-')} • 📅 {row.get('release_date','-')} • ⏱️ {int(d//60000)}:{int((d%60000)//1000):02d}</div>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Aucune donnée disponible. Lance une synchronisation !")