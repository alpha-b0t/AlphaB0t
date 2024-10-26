from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime

# Initialize the database and migrations
db = SQLAlchemy()
migrate = Migrate()

class User(db.Model):
    __tablename__ = "User"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(20), nullable=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

class ExchangeAccounts(db.Model):
    __tablename__ = "ExchangeAccounts"
    account_id = db.Column(db.Integer, primary_key=True)
    # Foreign key: user_id
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    exchange_name = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(64), nullable=False)
    api_secret = db.Column(db.String(64), nullable=False)
    api_passphrase = db.Column(db.String(64), nullable=True)

    def __init__(self, user_id, exchange_name, api_key, api_secret, api_passphrase=''):
        self.user_id = user_id
        self.exchange_name = exchange_name
        self.api_key = api_key
        self.api_secret = api_secret
        if api_passphrase != '':
            self.api_passphrase = api_passphrase