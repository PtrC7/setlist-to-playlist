from .setlists import setlist_bp
from .playlists import playlist_bp

def register_routes(app):
    app.register_blueprint(setlist_bp, url_prefix='/api')
    app.register_blueprint(playlist_bp, url_prefix='/api')