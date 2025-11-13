from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import logging, time
from typing import List, Optional

from api.models import Song, SetListInfo
from api.exceptions import APIError, AuthenticationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class SpotifyError(APIError):
    pass

def _is_valid_album(album_name: str) -> bool:
    name_lower = album_name.lower()
    invalid_keywords = ["compilation", "greatest hits", "remaster", "live", "version"]
    return not any(word in name_lower for word in invalid_keywords)

class SpotifyAppClient:
    def __init__(self, client_id, client_secret):
        if not client_id or not client_secret:
            raise AuthenticationError("Spotify API credentials not found")
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
        )

    def get_artist_image(self, artist_id: str) -> Optional[str]:
        try:
            artist = self.sp.artist(artist_id)
            images = artist.get("images", [])
            return images[0]["url"] if images else None
        except Exception as e:
            logger.warning(f"Error fetching artist image: {e}")
            return None

    def search_track(self, song: Song):
        query = f"track:{song.name} artist:{song.original_artist}"
        logger.info(f"[App] Spotify search: {query}")
        try:
            results = self.sp.search(q=query, type="track", limit=5)
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                return None

            filtered = [t for t in tracks if _is_valid_album(t["album"]["name"])]

            def artist_match(t):
                return any(a["name"].lower() == song.original_artist.lower() for a in t["artists"])

            filtered = [t for t in filtered if artist_match(t)] or filtered
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
            logger.warning(f"[App] Spotify search failed for {query}: {e}")
            return None

class SpotifyUserClient:
    def __init__(self, access_token: str):
        if not access_token:
            raise AuthenticationError("Missing Spotify user access token")
        self.sp = spotipy.Spotify(auth=access_token)
        self.user_id = self.sp.me()["id"]

    def create_playlist_from_setlist(self, setlist: SetListInfo, songs: List[Song], search_with_app: SpotifyAppClient, public: bool):
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
            track_data = search_with_app.search_track(song)
            if track_data and track_data["uri"]:
                track_uris.append(track_data["uri"])

        if track_uris:
            self.sp.playlist_add_items(playlist["id"], track_uris)

        return playlist["external_urls"]["spotify"]
