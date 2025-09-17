from api.setlistfm import SetlistFMClient
from api.spotify import SpotifyClient
from dotenv import load_dotenv
import os

load_dotenv()

def test_spotify_playlist(artist_name):
    setlist_api_key = os.getenv("SETLISTFM_API_KEY")
    setlist_client = SetlistFMClient(setlist_api_key)

    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    cache_path = None
    spotify_client = SpotifyClient(spotify_client_id, spotify_client_secret, redirect_uri, cache_path)

    setlists = setlist_client.get_recent_setlists(artist_name, limit=5)
    for idx, setlist in enumerate(setlists):
        print(f"{idx}. {setlist.artist} - {setlist.tour} - {setlist.city} - {setlist.venue} - {setlist.date}\n")
    
    pos = input("Select a Setlist: ")
    setlist = setlists[int(pos)]

    songs = setlist_client.get_setlist_songs(setlist.id)

    playlist_url = spotify_client.create_playlist_from_setlist(setlist, songs, public=True)

    print(f"Playlist created: {playlist_url}")