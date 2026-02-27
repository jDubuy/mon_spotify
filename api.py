# api.py
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd

# Ajouter le répertoire courant au chemin pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import load_full_history, get_setting, save_setting
from bot import fetch_history

app = FastAPI(title="Mon Spotify API")

# Configuration du CORS pour permettre au Frontend de discuter avec le Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # À restreindre en production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/")
def read_root():
    """Sert la page HTML principale"""
    return FileResponse("index.html")

@app.get("/api/history")
def get_history():
    """Récupère l'historique complet au format JSON"""
    df = load_full_history()
    if df.empty:
        return []
    # Conversion du dataframe en dictionnaire pour le JSON
    return df.to_dict(orient="records")

@app.get("/api/stats")
def get_stats():
    """Calcule les statistiques clés pour le dashboard"""
    df = load_full_history()
    if df.empty:
        return {"total_tracks": 0, "unique_artists": 0}
    
    return {
        "total_tracks": len(df),
        "unique_artists": df['artist_name'].nunique(),
        "avg_duration": df['duration_ms'].mean() if 'duration_ms' in df else 0
    }

@app.post("/api/sync")
def trigger_sync():
    """Déclenche la synchronisation Spotify via le bot"""
    try:
        nouveaux = fetch_history.main()
        return {"status": "success", "added": len(nouveaux), "tracks": nouveaux}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings/{key}")
def read_setting(key: str):
    """Lit un réglage en base"""
    value = get_setting(key)
    return {"key": key, "value": value}

@app.post("/api/settings")
def update_setting(key: str, value: str):
    """Enregistre un réglage"""
    save_setting(key, value)
    return {"status": "saved"}

@app.get("/api/top-artists")
def get_top_artists(limit: int = 3):
    """Récupère le top des artistes avec une image représentative"""
    df = load_full_history()
    if df.empty: return []
    
    # Groupement et comptage
    top = df.groupby('artist_name').agg({
        'played_at': 'count',
        'album_cover_url': 'first'  # On prend la pochette du morceau le plus récent
    }).reset_index().rename(columns={'played_at': 'count'})
    
    return top.sort_values('count', ascending=False).head(limit).to_dict(orient="records")

@app.get("/api/top-tracks")
def get_top_tracks(limit: int = 3):
    """Récupère le top des titres avec leurs pochettes"""
    df = load_full_history()
    if df.empty: return []
    
    top = df.groupby(['track_name', 'artist_name']).agg({
        'played_at': 'count',
        'album_cover_url': 'first'
    }).reset_index().rename(columns={'played_at': 'count'})
    
    return top.sort_values('count', ascending=False).head(limit).to_dict(orient="records")