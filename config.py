import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # API Keys
    SETLISTFM_API_KEY = os.getenv('SETLISTFM_API_KEY')
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI',)
    
    # Cache settings
    CACHE_TTL = 300  # 5 minutes