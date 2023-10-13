from flask import Flask
from views.api import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run()