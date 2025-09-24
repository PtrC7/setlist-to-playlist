from flask import Blueprint, request, jsonify, current_app
from api.setlistfm import SetlistFMClient
from api.exceptions import APIError, NotFoundError

setlist_bp = Blueprint('setlists', __name__)

def get_setlistfm_client():
    return SetlistFMClient(
        api_key=current_app.config['SETLISTFM_API_KEY'],
        cache_ttl=current_app.config['CACHE_TTL']
    )

@setlist_bp.route('/artists/search', methods=['GET'])
def search_artists():
    try:
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))

        if not query:
            return jsonify({'error': 'Query parameter required'}), 400
        
        client = get_setlistfm_client()
        artists = client.search_artist(query, page)

        return jsonify ({
            'success': True,
            'data': artists,
            'page': page
        })
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
    
@setlist_bp.route('/artists/<mbid>/setlists', methods=['Get'])
def get_artist_setlists(mbid):
    try:
        page = int(request.args.get('page', 1))

        client = get_setlistfm_client()
        setlists = client.get_artist_setlists(mbid, page)

        return jsonify({
            'success': True,
            'data': setlists,
            'page': page
        })
    
    except NotFoundError as e:
        return jsonify({'error', str(e)}), 404
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    
@setlist_bp.route('/setlists/<setlist_id>', methods=['GET'])
def get_setlist_details(setlist_id):
    try:
        client = get_setlistfm_client()
        songs = client.get_setlist_songs(setlist_id)

        return jsonify({
            'success': True,
            'data': {
                'setlist_id': setlist_id,
                'songs': [
                    {
                        'name': song.name,
                        'artist': song.artist,
                        'original_artist': song.original_artist,
                        'is_cover': song.is_cover,
                        'is_encore': song.is_encore,
                        'encore': song.encore,
                        'position': song.position,
                        'set_number': song.set_number,
                        'info': song.info
                    } for song in songs
                ]
            }
        })
    
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except APIError as e:
        return jsonify({'error': str(e)}), 500


@setlist_bp.route('/artists/<artist_name>/recent', methods=['GET'])
def get_recent_setlists(artist_name):
    """Get recent setlists for an artist"""
    try:
        days = int(request.args.get('days', 365))
        limit = int(request.args.get('limit', 20))
        
        client = get_setlistfm_client()
        setlists = client.get_recent_setlists(artist_name, days, limit)
        
        # Convert SetListInfo objects to dictionaries
        setlists_data = [
            {
                'id': setlist.id,
                'artist': setlist.artist,
                'date': setlist.date,
                'venue': setlist.venue,
                'city': setlist.city,
                'country': setlist.country,
                'tour': setlist.tour,
                'url': setlist.url,
                'display_title': setlist.display_title
            } for setlist in setlists
        ]
        
        return jsonify({
            'success': True,
            'data': setlists_data
        })
        
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except APIError as e:
        return jsonify({'error': str(e)}), 500