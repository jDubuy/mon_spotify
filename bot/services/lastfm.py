import requests
import os

def fetch_genres(artist_name: str) -> str:
    """Isolons la logique Last.fm"""
    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key: return ""
    
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.getTopTags",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json"
    }
    try:
        res = requests.get(url, params=params, timeout=5).json()
        tags = res.get('toptags', {}).get('tag', [])
        return ", ".join([t['name'] for t in tags[:3]])
    except Exception:
        return ""