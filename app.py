import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bot import fetch_history

# Configuration de la page
load_dotenv()
st.set_page_config(page_title="Spotify Dashboard Pro", page_icon="🟢", layout="wide")

# --- ÉTAT DE SESSION ---
if 'history_limit' not in st.session_state:
    st.session_state.history_limit = 20

# --- FONCTIONS DE PERSISTANCE ---

def get_db_setting(key, default=None):
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else default

def save_db_setting(key, value):
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# --- FONCTIONS DE DONNÉES ---

@st.cache_data
def load_data():
    conn = sqlite3.connect('spotify_data.db', timeout=20)
    query = '''
        SELECT 
            h.played_at, 
            t.track_name, 
            t.artist_name, 
            t.duration_ms, 
            alb.album_cover_url, 
            art.artist_genres, 
            alb.album_name, 
            alb.release_date
        FROM history h
        JOIN tracks t ON h.track_id = t.track_id
        JOIN artists art ON t.artist_name = art.artist_name
        JOIN albums alb ON t.album_name = alb.album_name AND t.artist_name = alb.artist_name
    '''
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Erreur DB : {e}")
        df = pd.DataFrame()
    conn.close()
    
    if not df.empty:
        df['played_at'] = pd.to_datetime(df['played_at']).dt.tz_convert('Europe/Paris')
    return df

def get_artist_bio(artist_name):
    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key: return None
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {"method": "artist.getInfo", "artist": artist_name, "api_key": api_key, "format": "json", "lang": "fr"}
    try:
        res = requests.get(url, params=params, timeout=5).json()
        return res.get('artist')
    except: return None

# --- MICRO-PAGES (DIALOGS) ---

@st.dialog("Fiche de l'Artiste")
def show_artist_card(artist_name, df_full):
    with st.spinner("Chargement..."):
        bio = get_artist_bio(artist_name)
    if bio:
        artist_rows = df_full[df_full['artist_name'].str.contains(artist_name, na=False)]
        img_path = artist_rows.iloc[0]['album_cover_url'] if not artist_rows.empty else ""
        col1, col2 = st.columns([1, 2])
        with col1:
            # Correction syntaxe width='stretch'
            st.image(img_path if img_path and str(img_path).strip() != "" else "https://www.scdn.co/scannables/svg/only-logo/255/white", width='stretch')
            st.metric("Écoutes", len(artist_rows))
        with col2:
            st.subheader(bio['name'])
            st.write(bio.get('bio', {}).get('summary', "").split('<a href')[0])

# --- CHARGEMENT ---
df_raw = load_data()

# --- STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    h1, h2, h3 { color: #1DB954 !important; }
    [data-testid="stMetric"] { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border-left: 5px solid #1DB954; }
    .mosaic-container { position: relative; width: 100%; border-radius: 10px; overflow: hidden; transition: transform 0.3s ease; }
    .mosaic-container:hover { transform: scale(1.1); z-index: 10; }
    .mosaic-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; pointer-events: none; }
    .mosaic-container:hover .mosaic-overlay { opacity: 1; }
    .artist-name-hover { color: #1DB954; font-weight: bold; }
    .artist-link-clean button { background: transparent !important; border: none !important; padding: 0 !important; color: #1DB954 !important; font-size: 1.1rem !important; }
    .track-card { background: rgba(255,255,255,0.02); padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.05); }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.title("🟢 Spotify Menu")
    if st.button('📡 Synchro Spotify'):
        fetch_history.main()
        st.cache_data.clear()
        st.rerun()
    filtre = st.selectbox("Période :", ["12h", "3 jours", "7 jours", "1 mois", "Tout"], index=2, on_change=lambda: st.session_state.update(history_limit=20))
    batch_size = st.slider("Quantité par chargement", 10, 100, 20)

# --- NAVIGATION ---
tab_dash, tab_wall, tab_recs = st.tabs(["📊 Dashboard", "🖼️ Mosaïque", "🎵 Recommandations"])

if not df_raw.empty:
    maintenant = pd.Timestamp.now(tz='Europe/Paris')
    dates_map = {"12h": maintenant - timedelta(hours=12), "3 jours": maintenant - timedelta(days=3), "7 jours": maintenant - timedelta(days=7), "1 mois": maintenant - timedelta(days=30), "Tout": df_raw['played_at'].min()}
    df = df_raw[df_raw['played_at'] >= dates_map[filtre]].copy()

    with tab_dash:
        col_kpi, col_graphs = st.columns([1, 3], gap="large")
        with col_kpi:
            st.subheader("🖼️ Ma Vitrine")
            saved_url = get_db_setting('selected_pochette')
            if not saved_url:
                saved_url = df_raw.sort_values('played_at', ascending=False).iloc[0]['album_cover_url']
            # Correction width='stretch'
            st.image(saved_url if saved_url and str(saved_url).strip() != "" else "https://www.scdn.co/scannables/svg/only-logo/255/white", width='stretch')
            st.divider()
            st.metric("🎵 Titres (Total)", len(df))
            st.metric("🎶 Titres Distincts", df['track_name'].nunique())
            st.metric("🎤 Artistes", df['artist_name'].nunique())
            avg_ms = df['duration_ms'].mean() if not df.empty else 0
            st.metric("⏳ Durée Moyenne", f"{int(avg_ms//60000)}:{int((avg_ms%60000)//1000):02d}")

        with col_graphs:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🏆 Top Artistes")
                top_a = df.groupby('artist_name').agg({'played_at': 'count'}).reset_index().rename(columns={'played_at': 'Écoutes'}).sort_values('Écoutes', ascending=True).tail(8)
                fig_a = px.bar(top_a, y='artist_name', x='Écoutes', orientation='h', color_discrete_sequence=['#1DB954'])
                fig_a.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=320, xaxis_title=None, yaxis_title=None)
                # Correction width='stretch'
                st.plotly_chart(fig_a, width='stretch')
            with c2:
                st.subheader("🔁 Top Titres")
                top_t = df.groupby('track_name').agg({'played_at': 'count'}).reset_index().rename(columns={'played_at': 'Écoutes'}).sort_values('Écoutes', ascending=True).tail(8)
                fig_t = px.bar(top_t, y='track_name', x='Écoutes', orientation='h', color_discrete_sequence=['#1DB954'])
                fig_t.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=320, xaxis_title=None, yaxis_title=None)
                # Correction width='stretch'
                st.plotly_chart(fig_t, width='stretch')

            st.divider()
            st.subheader("🎸 Genres Dominants")
            all_genres = []
            if 'artist_genres' in df.columns:
                for g in df['artist_genres'].dropna():
                    if g: all_genres.extend([x.strip().capitalize() for x in g.split(',')])
            if all_genres:
                g_counts = pd.Series(all_genres).value_counts().head(10).reset_index()
                fig_g = px.bar(g_counts, x='count', y='index', orientation='h', color_discrete_sequence=['#1DB954'])
                fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=350, xaxis_title=None, yaxis_title=None)
                # Correction width='stretch'
                st.plotly_chart(fig_g, width='stretch')

        st.divider()
        st.subheader("📜 Historique")
        search = st.text_input("🔍 Rechercher...")
        df_filtered = df.copy()
        if search:
            df_filtered = df[df['track_name'].str.contains(search, case=False, na=False) | 
                             df['artist_name'].str.contains(search, case=False, na=False)]
        
        recent = df_filtered.sort_values('played_at', ascending=False).head(st.session_state.history_limit)
        for _, row in recent.iterrows():
            with st.container():
                st.markdown('<div class="track-card">', unsafe_allow_html=True)
                ci, ctx = st.columns([1.5, 8.5])
                with ci:
                    st.image(row.get('album_cover_url', '') if row.get('album_cover_url') else "https://www.scdn.co/scannables/svg/only-logo/255/white", width=100)
                with ctx:
                    st.markdown(f"<h3 style='margin:0;'>{row['track_name']}</h3>", unsafe_allow_html=True)
                    art = row['artist_name'].split(',')[0]
                    st.markdown('<div class="artist-link-clean">', unsafe_allow_html=True)
                    if st.button(art, key=f"dash_{row['played_at']}"): show_artist_card(art, df_raw)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        if len(df_filtered) > st.session_state.history_limit:
            # Correction width='stretch'
            if st.button(f"➕ Charger {batch_size} titres", width='stretch'):
                st.session_state.history_limit += batch_size
                st.rerun()

    with tab_wall:
        st.title("🖼️ Mur de Pochettes")
        all_covers = df_raw[df_raw['album_cover_url'].str.strip() != ""].drop_duplicates('album_cover_url').sort_values('played_at', ascending=False)
        cols_per_row = 8
        for i in range(0, len(all_covers), cols_per_row):
            row_data = all_covers.iloc[i : i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, (_, song) in enumerate(row_data.iterrows()):
                with cols[j]:
                    st.markdown(f'<div class="mosaic-container"><img src="{song["album_cover_url"]}" style="width:100%;"><div class="mosaic-overlay"><span class="artist-name-hover">{song["artist_name"].split(",")[0]}</span></div></div>', unsafe_allow_html=True)
                    # Correction width='stretch'
                    if st.button("Sél.", key=f"wall_{song['album_cover_url']}", width='stretch'):
                        save_db_setting('selected_pochette', song['album_cover_url'])
                        st.rerun()

    with tab_recs:
        st.title("🎯 Recommandations")
        if st.button("🔄 Rafraîchir"): st.cache_data.clear()
        sp = fetch_history.get_spotify_client()
        recommendations = fetch_history.get_recommendations(sp, limit=12)
        if recommendations:
            cols = st.columns(3)
            for idx, track in enumerate(recommendations):
                with cols[idx % 3]:
                    st.markdown(f"""<div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; margin-bottom: 20px;"><img src="{track['cover']}" style="width:100%; border-radius: 10px;"><h4 style="margin:0; color:#1DB954;">{track['name']}</h4><p style="margin:0; color:#B3B3B3;">{track['artist']}</p><a href="{track['url']}" target="_blank"><button style="width:100%; background:#1DB954; color:white; border:none; padding:8px; border-radius:20px; cursor:pointer;">🎧 Spotify</button></a></div>""", unsafe_allow_html=True)
else:
    st.info("Lancez une synchronisation !")