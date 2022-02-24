from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import sys

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['JSON_AS_ASCII'] = False
    app.config['SECRET_KEY'] = 'pskateboard-wtf'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User, Item

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for rest-api parts of app
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    app.register_error_handler(404, main.not_found_page)
    app.register_error_handler(500, main.server_error_page)
    sys.setrecursionlimit(10000)

    return app