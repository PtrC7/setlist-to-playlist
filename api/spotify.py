from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from typing import List, Optional

from api.models import Song, SetListInfo
from api.exceptions import APIError, AuthenticationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class SpotifyError(APIError):
    pass


class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri, cache_path=".spotify_cache"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        if not self.client_id or not self.client_secret:
            raise AuthenticationError("Spotify API credentials not found")
        
        scope = "playlist-modify-public playlist-modify-private user-read-email"
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

    def get_artist_image(self, artist_id: str) -> Optional[str]:
        """Get the artist’s Spotify profile image"""
        try:
            artist = self.sp.artist(artist_id)
            images = artist.get("images", [])
            if images:
                return images[0]["url"]
        except Exception as e:
            logger.warning(f"Error fetching artist image: {e}")
        return None


    def search_track(self, song: Song):
        query = f"track:{song.name} artist:{song.original_artist}"
        logger.info(f"Spotify search: {query}")

        try:
            results = self.sp.search(q=query, type="track", limit=5)
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                return None

            # Filter out non-original albums
            def is_valid_album(album_name):
                name_lower = album_name.lower()
                invalid_keywords = ["compilation", "greatest hits", "remaster", "live", "version"]
                return not any(word in name_lower for word in invalid_keywords)

            filtered = [t for t in tracks if is_valid_album(t["album"]["name"])]

            # Prefer results where the primary artist matches exactly
            def artist_match(t):
                return any(
                    a["name"].lower() == song.original_artist.lower() for a in t["artists"]
                )

            filtered = [t for t in filtered if artist_match(t)] or filtered

            # Choose the first filtered result
            track = filtered[0]

            artist_id = track["artists"][0]["id"]
            artist_image = self.get_artist_image(artist_id)

            return {
                "uri": track["uri"],
                "name": track["name"],
                "album": track["album"]["name"],
                "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "artist_image": artist_image,
            }

        except Exception as e:
            logger.warning(f"Spotify search failed for {query}: {e}")
            return None



    def create_playlist_from_setlist(self, setlist: SetListInfo, songs: List[Song], public=False):
        playlist_name = setlist.display_title
        description = f"Playlist generated from {setlist.url}"
        logger.info(f"Creating playlist: {playlist_name}")

        playlist = self.sp.user_playlist_create(
            user=self.user_id,
            name=playlist_name,
            public=public,
            description=description
        )

        track_uris = []
        for song in songs:
            track_data = self.search_track(song)
            if track_data and track_data["uri"]:
                track_uris.append(track_data["uri"])

        if track_uris:
            self.sp.playlist_add_items(playlist["id"], track_uris)
        
        return playlist["external_urls"]["spotify"]
