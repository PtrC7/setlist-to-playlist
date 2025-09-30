from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List
import logging

from api.models import Song, SetListInfo
from api.exceptions import (
    APIError, AuthenticationError
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class SpotifyError(APIError):
    pass

class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri, cache_path = ".spotify_cache"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        if not self.client_id or not self.client_secret:
            raise AuthenticationError("Spotify API credentials not found")
        
        scope = "playlist-modify-public playlist-modify-private"

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                cache_path=cache_path
            )
        )

        self.user_id = self.sp.me()["id"]
        
    def search_track(self, song: Song):
        query = f"track:{song.name} artist:{song.original_artist}"
        logger.info(f"Searching for {query} Tape: {song.tape}\n")

        results = self.sp.search(q=query, type="track", limit=1)
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            logger.warning(f"No match found for {song.name} by {song.original_artist}")
            return None

        return tracks[0]["uri"]
    
    def create_playlist_from_setlist(self, setlist: SetListInfo, songs: List[Song], public: bool = False):
        playlist_name = setlist.display_title
        description = f"Playlist generated from {setlist.url}"

        logger.info(f"Creating playlist: {playlist_name}")
        playlist = self.sp.user_playlist_create(
            user = self.user_id,
            name = playlist_name,
            public = public,
            description = description
        )

        track_uris = []

        for song in songs:
            uri = self.search_track(song)
            if uri:
                track_uris.append(uri)
        
        if track_uris:
            self.sp.playlist_add_items(playlist["id"], track_uris)
        else:
            logger.warning("No tracks found to add to the playlist")
        
        return playlist["external_urls"]["spotify"]