from dataclasses import dataclass
from datetime import datetime, timedelta

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
    url: str = ""
    venue_id: str = None
    artist_mbid: str = None

    @property
    def formatted_date(self):
        if not self.date:
            return None
        try:
            return datetime.strptime(self.date, '%m-%d-%Y')
        except ValueError:
            return None
    
    @property
    def display_title(self):
        return f"{self.artist} - {self.venue}, {self.city} ({self.date})"