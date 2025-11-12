from flask import Blueprint, request, jsonify, current_app, session
from api.spotify import SpotifyClient
from api.setlistfm import SetlistFMClient
from api.models import SetListInfo
from api.exceptions import APIError, AuthenticationError, NotFoundError

playlist_bp = Blueprint('playlists', __name__)

def get_spotify_client():
    try:
        return SpotifyClient(
            client_id=current_app.config['SPOTIFY_CLIENT_ID'],
            client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
            redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI']
        )
    except AuthenticationError as e:
        raise e

def get_setlistfm_client():
    return SetlistFMClient(
        api_key=current_app.config['SETLISTFM_API_KEY'],
        cache_ttl=current_app.config['CACHE_TTL']
    )

@playlist_bp.route('/playlists/create', methods=['POST'])
def create_playlist():
    try:
        data = request.get_json()
        if not data or 'setlist_id' not in data:
            return jsonify({'error': 'setlist_id required'}), 400

        setlist_id = data['setlist_id']
        public = data.get('public', False)

        setlistfm_client = get_setlistfm_client()
        all_songs = setlistfm_client.get_setlist_songs(setlist_id)

        # Build composite keys for server-side filtering
        def key_for(song):  # song is your Song dataclass
            return f"{song.set_number}-{song.position}"

        selected_keys = set(data.get('selected_keys') or [])
        if selected_keys:
            songs = [s for s in all_songs if key_for(s) in selected_keys]
        else:
            songs = all_songs  # fallback

        if not songs:
            return jsonify({'error': 'No selected songs to add'}), 400

        # (Optional) build setlist_info for name/desc as before
        setlist_info = SetListInfo(
            id=setlist_id,
            artist=songs[0].artist if songs else "Unknown Artist",
            date=data.get('date', ''),
            venue=data.get('venue', 'Unknown Venue'),
            city=data.get('city', 'Unknown City'),
            country=data.get('country', 'Unknown Country'),
            tour=data.get('tour'),
            url=f"https://setlist.fm/setlist/{setlist_id}"
        )

        spotify_client = get_spotify_client()
        playlist_url = spotify_client.create_playlist_from_setlist(setlist_info, songs, public)

        return jsonify({
            'success': True,
            'data': {
                'playlist_url': playlist_url,
                'songs_count': len(songs),
                'setlist_id': setlist_id
            }
        })
    except Exception as e:
        current_app.logger.exception("create_playlist failed")
        return jsonify({'error': 'Internal server error'}), 500

    
@playlist_bp.route('/playlists/preview', methods=['POST'])
def preview_playlist():
    """Preview what songs would be in a playlist"""
    try:
        data = request.get_json()
        
        if not data or 'setlist_id' not in data:
            return jsonify({'error': 'setlist_id required'}), 400
        
        setlist_id = data['setlist_id']
        
        # Get setlist songs
        setlistfm_client = get_setlistfm_client()
        all_songs = setlistfm_client.get_setlist_songs(setlist_id)

        selected_songs_data = data.get('songs')

        if selected_songs_data:
            # Match by both name and position (most reliable)
            selected_positions = {s['position'] for s in selected_songs_data}
            songs = [s for s in all_songs if s.position in selected_positions]
        else:
            songs = all_songs
        
        if not songs:
            return jsonify({'error': 'No songs found in setlist'}), 404
        
        # Try to find each song on Spotify
        spotify_client = get_spotify_client()
        preview_data = []
        
        for song in songs:
            track_uri = spotify_client.search_track(song)
            preview_data.append({
                'name': song.name,
                'artist': song.artist,
                'original_artist': song.original_artist,
                'is_cover': song.is_cover,
                'is_encore': song.is_encore,
                'position': song.position,
                'set_number': song.set_number,
                'album': track_uri['album'] if track_uri else None,
                'album_image': track_uri['album_image'] if track_uri else None,
                'artist_image': track_uri['artist_image'] if track_uri else None,
                'found_on_spotify': track_uri is not None,
                'spotify_uri': track_uri['uri'] if track_uri else None
            })
        
        found_count = sum(1 for item in preview_data if item['found_on_spotify'])
        
        return jsonify({
            'success': True,
            'data': {
                'songs': preview_data,
                'total_songs': len(songs),
                'found_on_spotify': found_count,
                'match_percentage': round((found_count / len(songs)) * 100, 1) if songs else 0
            }
        })
        
    except AuthenticationError as e:
        return jsonify({'error': f'Spotify authentication failed: {str(e)}'}), 401
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except APIError as e:
        return jsonify({'error': str(e)}), 500