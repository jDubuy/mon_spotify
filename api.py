import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import de tes modules
from utils.database import load_full_history
from bot.fetch_history import get_spotify_client

load_dotenv()

app = FastAPI(title="Spotify Hybrid Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES API (BASÉES SUR SQLITE) ---

@app.get("/api/stats")
def get_stats():
    df = load_full_history()
    if df.empty: return {"total_tracks": 0, "unique_artists": 0}
    return {"total_tracks": len(df), "unique_artists": df['artist_name'].nunique()}

@app.get("/api/top-artists")
def get_sqlite_top_artists(limit: int = 3):
    df = load_full_history()
    if df.empty: return []
    top = df.groupby('artist_name').agg({'played_at': 'count', 'album_cover_url': 'first'}).reset_index()
    return top.sort_values('played_at', ascending=False).head(limit).to_dict(orient="records")

@app.get("/api/top-tracks")
def get_sqlite_top_tracks(limit: int = 3):
    df = load_full_history()
    if df.empty: return []
    top = df.groupby(['track_name', 'artist_name']).agg({'played_at': 'count', 'album_cover_url': 'first'}).reset_index()
    return top.sort_values('played_at', ascending=False).head(limit).to_dict(orient="records")

@app.get("/api/history")
def get_history():
    df = load_full_history()
    return df.sort_values('played_at', ascending=False).head(20).to_dict(orient="records") if not df.empty else []

# --- ROUTES API (OFFICIELLES SPOTIFY ALL-TIME) ---

@app.get("/api/official-top-artists")
def get_official_top_artists(limit: int = 5):
    sp = get_spotify_client()
    try:
        results = sp.current_user_top_artists(limit=limit, time_range='long_term')
        return [{
            'name': item['name'],
            'image': item['images'][0]['url'] if item['images'] else None,
            'genres': item['genres'][:2]
        } for item in results['items']]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/official-top-tracks")
def get_official_top_tracks(limit: int = 5):
    sp = get_spotify_client()
    try:
        results = sp.current_user_top_tracks(limit=limit, time_range='long_term')
        return [{
            'name': item['name'],
            'artist': item['artists'][0]['name'],
            'cover': item['album']['images'][0]['url'] if item['album']['images'] else None
        } for item in results['items']]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync")
def trigger_sync():
    from bot import fetch_history
    added = fetch_history.main()
    return {"status": "success", "added": len(added)}

# Servir les fichiers statiques
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)