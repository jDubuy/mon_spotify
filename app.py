import pandas as pd
import streamlit as st
import plotly.express as px
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bot import fetch_history
from utils.database import get_setting, save_setting, load_full_history

# --- CONFIGURATION INITIALE ---
load_dotenv()
st.set_page_config(page_title="Spotify Dashboard Pro", page_icon="🟢", layout="wide")

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CHARGEMENT DU STYLE ---
def load_css(file_path):
    """Charge le design depuis le fichier CSS externe"""
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"Le fichier de style {file_path} est introuvable.")

load_css("assets/style.css")

# --- GESTION DE L'ÉTAT ---
if 'history_limit' not in st.session_state:
    st.session_state.history_limit = 20

# Constantes visuelles
SPOTIFY_LOGO = "https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png"
SPOTIFY_GREEN = "#1DB954"
# Échelle de vert "GitHub Style"
GREEN_SCALE = ['#121212', '#0e4429', '#006d32', '#26a641', '#39d353']

# --- SERVICES DE DONNÉES ---

@st.cache_data
def load_data():
    """Charge l'historique en utilisant l'utilitaire de base de données"""
    try:
        df = load_full_history()
        if not df.empty:
            df['played_at'] = pd.to_datetime(df['played_at']).dt.tz_convert('Europe/Paris')
        return df
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()

def get_artist_bio(artist_name):
    """Cherche la biographie de l'artiste sur Last.fm"""
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
    """Affiche les détails de l'artiste dans une popup"""
    with st.spinner("Chargement..."):
        bio = get_artist_bio(artist_name)
    if bio:
        artist_rows = df_full[df_full['artist_name'].str.contains(artist_name, na=False)]
        img = artist_rows.iloc[0]['album_cover_url'] if not artist_rows.empty else SPOTIFY_LOGO
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(img if img and str(img).strip() != "" else SPOTIFY_LOGO, width='stretch')
            st.metric("Écoutes", len(artist_rows))
        with col2:
            st.subheader(bio['name'])
            st.write(bio.get('bio', {}).get('summary', "").split('<a href')[0])

# --- LOGIQUE PRINCIPALE ---

df_raw = load_data()

# Barre latérale (Sidebar)
with st.sidebar:
    st.title("🟢 Spotify Menu")
    if st.button('📡 Synchro Spotify'):
        fetch_history.main()
        st.cache_data.clear()
        st.rerun()
    
    filtre = st.selectbox(
        "Période :", 
        ["12h", "3 jours", "7 jours", "1 mois", "Tout"], 
        index=4, 
        on_change=lambda: st.session_state.update(history_limit=20)
    )
    st.divider()
    batch_size = st.slider("Quantité par chargement", 10, 100, 20)

# Onglets de navigation
tab_dash, tab_habits, tab_wall, tab_recs = st.tabs(["📊 Dashboard", "📅 Habitudes", "🖼️ Mosaïque", "🎯 Recommandations"])

if not df_raw.empty:
    now = pd.Timestamp.now(tz='Europe/Paris')
    d_map = {"12h": now - timedelta(hours=12), "3 jours": now - timedelta(days=3), 
             "7 jours": now - timedelta(days=7), "1 mois": now - timedelta(days=30), "Tout": df_raw['played_at'].min()}
    df = df_raw[df_raw['played_at'] >= d_map[filtre]].copy()

    # --- ONGLET 1 : DASHBOARD ---
    with tab_dash:
        col_kpi, col_graphs = st.columns([1, 3], gap="large")
        with col_kpi:
            st.subheader("🖼️ Ma Vitrine")
            saved_url = get_setting('selected_pochette')
            if not saved_url:
                saved_url = df_raw.sort_values('played_at', ascending=False).iloc[0]['album_cover_url']
            st.image(saved_url if saved_url else SPOTIFY_LOGO, width='stretch')
            
            st.divider()
            st.metric("🎵 Titres (Total)", len(df))
            st.metric("🎤 Artistes", df['artist_name'].nunique())
            avg = df['duration_ms'].mean() if not df.empty else 0
            st.metric("⏳ Durée Moyenne", f"{int(avg//60000)}:{int((avg%60000)//1000):02d}")

        with col_graphs:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🏆 Top Artistes")
                top_a = df.groupby('artist_name').size().reset_index(name='c').sort_values('c').tail(8)
                fig_a = px.bar(top_a, y='artist_name', x='c', orientation='h', color_discrete_sequence=[SPOTIFY_GREEN])
                fig_a.update_traces(hovertemplate="<b>%{y}</b><br>Écoutes : %{x}<extra></extra>")
                fig_a.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=320, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_a, width='stretch')
            with c2:
                st.subheader("🔁 Top Titres")
                top_t = df.groupby('track_name').size().reset_index(name='c').sort_values('c').tail(8)
                fig_t = px.bar(top_t, y='track_name', x='c', orientation='h', color_discrete_sequence=[SPOTIFY_GREEN])
                fig_t.update_traces(hovertemplate="<b>%{y}</b><br>Écoutes : %{x}<extra></extra>")
                fig_t.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=320, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_t, width='stretch')

    # --- ONGLET 2 : HABITUDES (Heatmap & Légende) ---
    with tab_habits:
        st.title("📅 Analyse Temporelle")
        col_group, col_leg = st.columns([2, 1])
        with col_group:
            mode = st.radio("Vue :", ["Heures / Jours", "Semaines / Jours"], horizontal=True)
        with col_leg:
            # Légende style GitHub
            st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 5px; font-size: 0.8rem; color: #b3b3b3; margin-top: 10px;">
                    <span>Moins</span>
                    <div style="width: 12px; height: 12px; background-color: {GREEN_SCALE[0]}; border: 1px solid #333;"></div>
                    <div style="width: 12px; height: 12px; background-color: {GREEN_SCALE[1]}; border: 1px solid #333;"></div>
                    <div style="width: 12px; height: 12px; background-color: {GREEN_SCALE[2]}; border: 1px solid #333;"></div>
                    <div style="width: 12px; height: 12px; background-color: {GREEN_SCALE[3]}; border: 1px solid #333;"></div>
                    <div style="width: 12px; height: 12px; background-color: {GREEN_SCALE[4]}; border: 1px solid #333;"></div>
                    <span>Plus</span>
                </div>
            """, unsafe_allow_html=True)

        h_df = df.copy()
        jours_ordre = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        jours_map = {'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mer', 'Thursday': 'Jeu', 'Friday': 'Ven', 'Saturday': 'Sam', 'Sunday': 'Dim'}
        h_df['Jour'] = h_df['played_at'].dt.day_name().map(jours_map)
        
        if mode == "Heures / Jours":
            h_df['Heure'] = h_df['played_at'].dt.hour
            fig = px.density_heatmap(h_df, x="Heure", y="Jour", nbinsx=24, color_continuous_scale=GREEN_SCALE, category_orders={'Jour': jours_ordre})
        else:
            h_df['Semaine'] = h_df['played_at'].dt.isocalendar().week
            fig = px.density_heatmap(h_df, x="Semaine", y="Jour", color_continuous_scale=GREEN_SCALE, category_orders={'Jour': jours_ordre})

        fig.update_traces(hovertemplate="<b>%{y}</b><br>Temps : %{x}<br>Intensité : %{z} titres<extra></extra>")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", coloraxis_showscale=False, height=400, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # --- ONGLET 3 : MOSAÏQUE ---
    with tab_wall:
        st.title("🖼️ Mur de Pochettes")
        ac = df_raw.drop_duplicates('album_cover_url').sort_values('played_at', ascending=False)
        cols_per_row = 8
        for i in range(0, len(ac), cols_per_row):
            row_data = ac.iloc[i : i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, (_, song) in enumerate(row_data.iterrows()):
                with cols[j]:
                    st.markdown(f'<div class="mosaic-container"><img src="{song["album_cover_url"]}" style="width:100%;"><div class="mosaic-overlay"><span class="artist-name-hover">{song["artist_name"].split(",")[0]}</span></div></div>', unsafe_allow_html=True)
                    if st.button("Sél.", key=f"w_{song['album_cover_url']}", width='stretch'):
                        save_setting('selected_pochette', song['album_cover_url'])
                        st.rerun()

    # --- ONGLET 4 : RECOMMANDATIONS ---
    with tab_recs:
        st.title("🎯 Recommandations")
        if st.button("🔄 Rafraîchir"): st.cache_data.clear()
        sp = fetch_history.get_spotify_client()
        recs = fetch_history.get_recommendations(sp, limit=12)
        if recs:
            cols = st.columns(3)
            for i, t in enumerate(recs):
                with cols[i % 3]:
                    st.markdown(f"""<div class="track-card">
                        <img src="{t['cover'] if t['cover'] else SPOTIFY_LOGO}" style="width:100%; border-radius: 10px; margin-bottom: 10px;">
                        <h4 style="margin:0; color:{SPOTIFY_GREEN};">{t['name']}</h4>
                        <p style="margin:0; color:#B3B3B3;">{t['artist']}</p>
                        <a href="{t['url']}" target="_blank"><button style="width:100%; background:{SPOTIFY_GREEN}; color:white; border:none; padding:8px; border-radius:20px; cursor:pointer; margin-top:10px;">🎧 Spotify</button></a>
                    </div>""", unsafe_allow_html=True)
else:
    st.info("Aucune donnée. Lancez une synchronisation !")