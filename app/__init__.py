import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialise extensions outside the factory so models can import them
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # ------------------------------------------------------------------ #
    # Configuration                                                        #
    # SECRET_KEY is read from the environment so it is never hard-coded.  #
    # A fallback is provided for local development only.                  #
    # ------------------------------------------------------------------ #
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-fallback-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///ada1.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG_BYPASS_STARTUP'] = False  # Set True in dev to skip passphrase gate

    # Initialise extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Register blueprints
    from .routes import main
    app.register_blueprint(main)

    # Make csrf_token() available in all templates (used in manual POST forms)
    from flask_wtf.csrf import CSRFProtect, generate_csrf
    CSRFProtect(app)

    @app.after_request
    def set_csrf_cookie(response):
        response.set_cookie('csrf_token', generate_csrf())
        return response

    return app
