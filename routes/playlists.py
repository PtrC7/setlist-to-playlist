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
        data = request.get_json() or {}
        setlist_id = data.get('setlist_id')
        if not setlist_id:
            return jsonify({'error': 'setlist_id required'}), 400

        public = data.get('public', False)
        selected_keys = data.get('selected') or []

        setlistfm_client = get_setlistfm_client()
        all_songs = setlistfm_client.get_setlist_songs(setlist_id)

        if selected_keys:
            keyset = {(int(k.get('set_number', 0)), int(k.get('position', 0))) for k in selected_keys}
            songs = [s for s in all_songs if (s.set_number, s.position) in keyset]
        else:
            songs = all_songs

        current_app.logger.info(
            f"[create_playlist] setlist_id={setlist_id} total={len(all_songs)} selected={len(songs)}"
        )

        if not songs:
            return jsonify({'error': 'No songs selected'}), 400

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

    except AuthenticationError as e:
        return jsonify({'error': f'Spotify authentication failed: {str(e)}'}), 401
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.exception("Unexpected error in create_playlist")
        return jsonify({'error': 'Internal server error'}), 500