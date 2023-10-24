from flask import Flask
from config import AppConfig
from app.database.data_access import *
from app.views.api import api_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    app.register_blueprint(api_bp)

    app_config = AppConfig()

    # Connect to the database
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{app_config.DATABASE_USERNAME}:{app_config.DATABASE_PASSWORD}@localhost:{app_config.DATABASE_PORT}/{app_config.DATABASE_NAME}"
    
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    return app