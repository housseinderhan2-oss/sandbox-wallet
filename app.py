from flask import Flask
from config import Config
from models import DatabaseManager
from routes import api_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    DatabaseManager.init_db()
    app.register_blueprint(api_blueprint)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=False)
