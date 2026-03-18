import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, render_template, request
from flask_caching import Cache
from flask_htmx import HTMX
from flask_migrate import Migrate
from flask_moment import Moment
from posthog import Posthog
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import db, mail
from app.admin_views import init_admin
from app.extensions.celery import init_celery

migrate = Migrate()
moment = Moment()
htmx = HTMX()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})

posthog = Posthog(os.getenv("POSTHOG_API_KEY", ""), host="https://eu.i.posthog.com")


def create_app():
    app = Flask(__name__)

    app.config["APP_NAME"] = os.getenv("APP_NAME", "Landing Page")
    app_settings = os.getenv("APP_SETTINGS")
    app.config.from_object(app_settings)
    app.config["MAINTENANCE_MODE"] = os.getenv("MAINTENANCE_MODE", "False") == "True"

    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.ionos.com")
    app.config["MAIL_PORT"] = os.getenv("MAIL_PORT", 587)
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "noreply@example.com")

    # Campaign config
    app.config["LEAD_EMAIL_SUBJECT"] = os.getenv("LEAD_EMAIL_SUBJECT", "Thanks for your interest!")
    app.config["AB_VARIANT"] = os.getenv("AB_VARIANT", "a")

    app.config.from_mapping(
        CELERY={
            "broker_url": app.config.get("REDIS_URL", "redis://localhost:6379/0"),
            "result_backend": app.config.get("REDIS_URL", "redis://localhost:6379/0"),
            "task_ignore_result": True,
        }
    )

    init_celery(app)
    init_admin(app)
    db.init_app(app)
    htmx.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)

    # Enable foreign key support for SQLite (dev only)
    if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            ac = dbapi_connection.autocommit
            dbapi_connection.autocommit = True
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            dbapi_connection.autocommit = ac

    from app.public import bp as public_bp
    app.register_blueprint(public_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    @app.before_request
    def check_for_maintenance():
        if (
            app.config["MAINTENANCE_MODE"]
            and request.blueprint != "public_bp"
            and not request.path.startswith("/static/")
        ):
            return render_template("errors/maintenance.html"), 503

    if app.debug:
        posthog.disabled = True
        app.logger.setLevel(logging.DEBUG)

    if not app.debug and not app.testing:
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        if app.config.get("LOG_TO_STDOUT", False):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            logs_path = Path("logs")
            if not logs_path.exists():
                logs_path.mkdir()
            file_handler = RotatingFileHandler(
                "logs/flask.log", maxBytes=10240, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            root.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1, x_prefix=1)
    return app


from app import models  # noqa: F401, E402
