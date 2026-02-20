from flask import Flask
from flask_cors import CORS
from config import AppConfig
from app.api import api_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    
    app.register_blueprint(api_bp)

    app_config = AppConfig()

    # Initialize CORS
    # https://flask-cors.corydolphin.com/en/latest/api.html#extension
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    return app