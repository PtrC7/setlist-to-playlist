import logging
from dotenv import load_dotenv

from api.models import Song, SetListInfo
from api.exceptions import (
    APIError, NotFoundError)
from api.utils import (
    RateLimiter, CacheManager, RequestHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class SetlistFMError(APIError):
    pass

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
                # if song_data.get('tape', False):
                    # continue
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
        
        return setlists
    
    def get_artist_setlists_filtered(
        self,
        artistmbid,
        page_limit=5,
        month=None,
        year=None,
        venue=None,
        tour=None
    ):
        results = []
        page = 1

        while page <= page_limit:
            setlists = self.get_artist_setlists(artistmbid, page)
            if not setlists:
                break

            for s in setlists:
                if (month or year) and s.formatted_date:
                    if month and s.formatted_date.month != int(month):
                        continue
                    if year and s.formatted_date.year != int(year):
                        continue

                if venue and venue.lower() not in (s.venue or "").lower():
                    continue

                if tour and tour.lower() not in (s.tour or "").lower():
                    continue

                results.append(s)

            page += 1

        return results
    
    def get_recent_setlists(self, artist_name, days = 365, limit = 20):
        artists = self.search_artist(artist_name)
        if not artists:
            raise NotFoundError(f"{artist_name} was not found")

        artist_mbid = artists[0]['mbid']
        all_setlists = []
        page = 1

        while len(all_setlists) < limit:
            setlists = self.get_artist_setlists(artist_mbid, page)
            if not setlists:
                break

            all_setlists.extend(setlists)
            page += 1
        
        return all_setlists
    
    def get_setlist_songs(self, setlist_id):
        endpoint = f'/setlist/{setlist_id}'
        data = self.request_handler.make_request(endpoint)
        songs = self.parser.parse_setlist_songs(data)
        return songs
