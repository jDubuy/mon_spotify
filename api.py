import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import de tes modules personnalisés
from utils.database import load_full_history, get_setting, save_setting
from bot import fetch_history

# Chargement des variables d'environnement
load_dotenv()

app = FastAPI(title="Spotify Hybrid API")

# Configuration CORS pour permettre au Frontend de communiquer avec le Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES API ---

@app.get("/api/stats")
def get_stats():
    """Retourne les chiffres clés du dashboard"""
    df = load_full_history()
    if df.empty:
        return {"total_tracks": 0, "unique_artists": 0}
    
    return {
        "total_tracks": len(df),
        "unique_artists": df['artist_name'].nunique()
    }

@app.get("/api/history")
def get_history():
    """Retourne l'historique complet d'écoute"""
    df = load_full_history()
    if df.empty:
        return []
    # Tri par date décroissante
    df = df.sort_values('played_at', ascending=False)
    return df.to_dict(orient="records")

@app.get("/api/top-artists")
def get_top_artists(limit: int = 3):
    """Calcule le classement des artistes pour le podium"""
    df = load_full_history()
    if df.empty: return []
    
    top = df.groupby('artist_name').agg({
        'played_at': 'count',
        'album_cover_url': 'first' # Image représentative
    }).reset_index().rename(columns={'played_at': 'count'})
    
    return top.sort_values('count', ascending=False).head(limit).to_dict(orient="records")

@app.get("/api/top-tracks")
def get_top_tracks(limit: int = 3):
    """Calcule le classement des titres pour le podium"""
    df = load_full_history()
    if df.empty: return []
    
    top = df.groupby(['track_name', 'artist_name']).agg({
        'played_at': 'count',
        'album_cover_url': 'first'
    }).reset_index().rename(columns={'played_at': 'count'})
    
    return top.sort_values('count', ascending=False).head(limit).to_dict(orient="records")

@app.get("/api/covers")
def get_unique_covers():
    """Récupère les pochettes uniques pour la page Mosaïque"""
    df = load_full_history()
    if df.empty: return []
    
    covers = df.drop_duplicates('album_cover_url').sort_values('played_at', ascending=False)
    return covers[['artist_name', 'album_name', 'album_cover_url']].to_dict(orient="records")

@app.post("/api/sync")
def trigger_sync():
    """Déclenche la synchronisation Spotify via ton bot"""
    try:
        # Appel de la fonction principale de ton bot
        added_tracks = fetch_history.main()
        return {"status": "success", "added": len(added_tracks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur synchro: {str(e)}")

# --- GESTION DES FICHIERS STATIQUES (SITE WEB) ---

# Cette ligne doit impérativement être à la FIN pour ne pas bloquer les routes /api
# Elle permet de servir index.html, mosaic.html et le dossier assets/
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)