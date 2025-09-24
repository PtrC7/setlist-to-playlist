from flask import Flask
from config import Config
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register all routes
    register_routes(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=app.config.get("PORT", 5000),
        debug=app.config.get("DEBUG", True)
    )