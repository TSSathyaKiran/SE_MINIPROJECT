from flask import Flask

from .config import CONFIGS
from .core.errors import register_error_handlers
from .extensions import db


def create_app(config_name="dev"):
    app = Flask(__name__)
    app.config.from_object(CONFIGS[config_name])
    db.init_app(app)
    register_error_handlers(app)

    from .modules import BLUEPRINTS, register_menu
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
    register_menu(app)

    with app.app_context():
        from . import models  # noqa: F401  (registers every table)
        db.create_all()
    return app
