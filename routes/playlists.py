from flask import Blueprint, request, jsonify, current_app, session
from api.spotify import SpotifyAppClient, SpotifyUserClient
from api.setlistfm import SetlistFMClient
from api.models import SetListInfo
from api.exceptions import APIError, AuthenticationError, NotFoundError

playlist_bp = Blueprint('playlists', __name__)

def get_spotify_app_client():
    return SpotifyAppClient(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET']
    )


def get_setlistfm_client():
    return SetlistFMClient(
        api_key=current_app.config['SETLISTFM_API_KEY'],
        cache_ttl=current_app.config['CACHE_TTL']
    )

@playlist_bp.route('/playlists/create', methods=['POST'])
def create_playlist():
    try:
        token = session.get("spotify_token")
        if not token or not token.get("access_token"):
            return jsonify({'error': 'Spotify login required'}), 401
        
        access_token = token.get("access_token")
        
        user_spotify = SpotifyUserClient(access_token=access_token)
        
        me = user_spotify.sp.me()
        print("Authenticated Spotify user (playlist):", me["id"], me.get("display_name"))

        app_spotify = get_spotify_app_client()

        data = request.get_json() or {}
        setlist_id = data.get('setlist_id')
        public = data.get('public', False)
        selected_keys = data.get('selected') or []

        setlistfm_client = get_setlistfm_client()
        all_songs = setlistfm_client.get_setlist_songs(setlist_id)

        if selected_keys:
            keyset = {(int(k.get('set_number', 0)), int(k.get('position', 0))) for k in selected_keys}
            songs = [s for s in all_songs if (s.set_number, s.position) in keyset]
        else:
            songs = all_songs

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

        playlist_url = user_spotify.create_playlist_from_setlist(setlist_info, songs, app_spotify, public)

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