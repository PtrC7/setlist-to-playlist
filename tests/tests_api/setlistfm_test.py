from api.setlistfm import SetlistFMClient
import os


def test_setlist_api(artist_name):
    api_key = os.getenv("SETLISTFM_API_KEY")
    client = SetlistFMClient(api_key)

    setlists = client.get_recent_setlists(artist_name)
    for idx, setlist in enumerate(setlists):
        print(f"{idx}. {setlist.artist} - {setlist.tour} - {setlist.city} - {setlist.venue} - {setlist.date}\n")

    pos = input("Select a Setlist: ")
    setlist = setlists[int(pos)]
    songs = client.get_setlist_songs(setlist.id)
    print(f"\n{setlist.artist} - {setlist.tour} - {setlist.city} - {setlist.venue} - {setlist.date}")
    print(setlist.url)
    for song in songs:
        print(f"{song.position}. {song.name} - {song.original_artist}")
