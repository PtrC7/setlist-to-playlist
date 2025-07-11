import requests
import os
import time
from datetime import datetime
import logging
import threading
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SetlistFMError(Exception):
    # Custom exception for setlist.fm API errors
    pass

class RateLimitError(SetlistFMError):
    # Rate limit is exceeded
    pass

class NotFoundError(SetlistFMError):
    # Resource is not found
    pass

class APIError(SetlistFMError):
    # General API errors
    pass

@dataclass
class Song:
    name: str
    artist: str
    encore: int = 0
    cover: str = None
    original_artist: str = None
    info: str = ""
    tape: bool = False
    position: int = 0
    set_number: int = 1

    def __post_init__(self):
        if not self.original_artist:
            self.original_artist = self.cover or self.artist
    
    @property
    def is_cover(self):
        return self.cover is not None
    
    @property
    def is_encore(self):
        return self.encore > 0
    

@dataclass
class SetListInfo:
    id: str
    artist: str
    date: str
    venue: str
    city: str
    country: str
    tour: str = None
    song_count: int = 0
    url: str = ""
    venue_id: str = None
    artist_mbid: str = None

    @property
    def formatted_date(self):
        if not self.date:
            return None
        try:
            return datetime.strptime(self.date, '%d-%m-%Y')
        except ValueError:
            return None
    
    @property
    def display_title(self):
        return f"{self.artist} - {self.venue}, {self.city} ({self.date})"
    
class RateLimiter:
    def __init__(self):
        self.max_requests = 2
        self.time_window = 1
        self.requests = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        with self.lock:
            now = time.time()

            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    self.requests.pop(0)

            self.requests.append(now)


class CacheManager:
    def __init__(self, default_ttl: 300):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            
            if time.time() - self.timestamps[key] > self.default_ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            return self.cache[key]
        
    def set(self, key, value, ttl = None):
        with self.lock:
            self.cache[key] = value
            self.timestamps[key] = time.time()

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()


class RequestHandler:
    def __init__(self, api_key, rate_limiter: RateLimiter, cache: CacheManager):
        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({
        "Accept": "application/json",
        "x-api-key": api_key,
        })
        self.base_url = "https://api.setlist.fm/rest/1.0"

    def make_request(self, endpoint, params = None, use_cache = True, max_retries = 3):
        cache_key = f"{endpoint}:{str(sorted((params or {}).items()))}"

        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_result
            
        for attempt in range(max_retries):
            try:
                self.rate_limiter.wait_if_needed()

                url = f"{self.base_url}/{endpoint.lstrip('/')}"

                logger.info(f"Making request to: {url} (attempt {attempt + 1})")
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {endpoint}")
                
                response.raise_for_status()
                result = response.json()

                if use_cache:
                    self.cache.set(cache_key, result)

                return result
            
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise APIError(f"Request timeout after {max_retries} attempts")
                time.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise APIError(f"Request failed: {e}")
                time.sleep(2 ** attempt)

        raise APIError("max retries exceeded")

class DataParser:
    @staticmethod
    def parse_artist_search(data):
        if 'artist' not in data:
            return []
        
        artists = []
        for artist_data in data['artist']:
            artist = {
                'name': artist_data.get('name', ''),
                'mbid': artist_data.get('mbid', ''),
                'disambiguation': artist_data.get('disambiguation', ''),
                'url': artist_data.get('url', '')
            }
            artists.append(artist)
        
        return artists

    @staticmethod
    def parse_setlist_search(data):
        if 'setlist' not in data:
            return []
        
        setlists = []
        for setlist_data in data['setlist']:
            setlist = DataParser.parse_setlist_info(setlist_data)
            setlists.append(setlist)
        
        return setlists
    
    @staticmethod
    def parse_setlist_info(setlist_data):
        venue_info = setlist_data.get('venue', {})
        city_info = venue_info.get('city', {})

        return SetListInfo(
            id=setlist_data.get('id', ''),
            artist=setlist_data.get('artist', {}).get('name', 'Unknown Artist'),
            date=setlist_data.get('eventDate', ''),
            venue=venue_info.get('name', 'Unknown Venue'),
            city=city_info.get('name', 'Unknown City'),
            country=city_info.get('country', {}).get('name', 'Unknown Country'),
            tour=setlist_data.get('tour', {}).get('name') if setlist_data.get('tour') else None,
            url=setlist_data.get('url', ''),
            venue_id=venue_info.get('id'),
            artist_mbid=setlist_data.get('artist', {}).get('mbid')
        )
    
    @staticmethod
    def parse_setlist_songs(setlist_data):
        songs = []

        if 'sets' not in setlist_data or 'set' not in setlist_data['sets']:
            return songs
        
        artist_name = setlist_data.get('artist', {}).get('name', 'Unknown Artist')

        for set_idx, set_data in enumerate(setlist_data['sets']['set']):
            if 'song' not in set_data:
                continue
            
            encore_level = set_data.get('encore', 0)

            for song_idx, song_data in enumerate(set_data['song']):
                if song_data.get('tape', False):
                    continue
                cover_info = song_data.get('cover', {})

                song = Song(
                    name=song_data.get('name', ''),
                    artist=artist_name,
                    encore=encore_level,
                    cover=cover_info.get('name') if cover_info else None,
                    original_artist=cover_info.get('name') if cover_info else artist_name,
                    info=song_data.get('info', ''),
                    tape=song_data.get('tape', False),
                    position=song_idx + 1,
                    set_number=set_idx + 1
                )
                songs.append(song)

        return songs

    


class SetlistFMClient:
    def __init__(self, api_key, cache_ttl = 300):
        self.api_key = api_key
        self.rate_limiter = RateLimiter()
        self.cache = CacheManager(default_ttl=cache_ttl)
        self.request_handler = RequestHandler(api_key, self.rate_limiter, self.cache)
        self.parser = DataParser()


    def search_artist(self, artist_name, page = 1):
        print(f"\nSearching for artist: {artist_name}")
        params = {
            'artistName': artist_name,
            'p': page,
            'sort': 'relevance'
        }
        data = self.request_handler.make_request('search/artists', params)

        return self.parser.parse_artist_search(data)
    
    def get_artist_setlists(self, artistmbid, page = 1):
        endpoint = f'/artist/{artistmbid}/setlists'
        params = {'p': page}

        data = self.request_handler.make_request(endpoint, params)
        setlists = self.parser.parse_setlist_search(data)
        
        for setlist in setlists:
            try:
                songs = self.get_setlist_songs(setlist.id)
                setlist.song_count = len(songs)
            except Exception as e:
                logger.warning(f"Could not get song count for setlist {setlist.id}: {e}")
        
        return setlists
    
    def get_setlist_songs(self, setlist_id):
        endpoint = f'/setlist/{setlist_id}'
        data = self.request_handler.make_request(endpoint)
        songs = self.parser.parse_setlist_songs(data)
        return songs








def main():
    api_key = os.getenv("SETLISTFM_API_KEY")
    client = SetlistFMClient(api_key)

    artists = client.search_artist("Playboi Carti")

    artist = artists[0]
    artist_mbid = artist['mbid']

    print(f'\n{artist}\n')
    print(f'\n{artist_mbid}\n')

    setlists = client.get_artist_setlists(artist_mbid)

    setlist = setlists[2]
    print(f'\n{setlist}\n')
    songs = client.get_setlist_songs(setlist.id)
    print(f'\n{songs}\n')


if __name__ == "__main__":
    main()