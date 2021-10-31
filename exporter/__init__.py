from flask import Flask
from werkzeug.exceptions import HTTPException

from .config import Config
from .errors import handle_http_exceptions
from .controllers import export_bp


def create_app(config_object: Config) -> Flask:
    app = Flask("converter", instance_relative_config=True)
    app.config.from_object(config_object)
    app.register_error_handler(HTTPException, handle_http_exceptions)
    _register_routes(app)
    return app


def _register_routes(app: Flask) -> None:
    app.register_blueprint(export_bp)
