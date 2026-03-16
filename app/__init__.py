import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(get_remote_address, storage_uri="memory://")

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__, 
                template_folder="../templates",
                static_folder="../static")
    
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "main.login"

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app