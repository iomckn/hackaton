from flask import Flask
from routes_pages import pages_bp
from routes_api import api_bp
from services.loader import load_collisions

def create_app():
    app = Flask(__name__)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)