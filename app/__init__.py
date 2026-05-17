from pathlib import Path

from flask import Flask

from .config import Config
from .extensions import limiter
from .routes import main_bp
from .utils.cleanup import cleanup_old_files


def create_app() -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )
    app.config.from_object(Config)

    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    app.config["PROCESSED_FOLDER"].mkdir(parents=True, exist_ok=True)

    limiter.init_app(app)
    app.register_blueprint(main_bp)

    @app.before_request
    def auto_cleanup_temp_files() -> None:
        cleanup_old_files(
            folders=[
                app.config["UPLOAD_FOLDER"],
                app.config["PROCESSED_FOLDER"],
            ],
            max_age_seconds=app.config["TEMP_FILE_MAX_AGE_SECONDS"],
            min_interval_seconds=app.config["CLEANUP_INTERVAL_SECONDS"],
        )

    @app.errorhandler(413)
    def payload_too_large(_error):
        return {
            "ok": False,
            "error": "File is too large. Max upload size is 25MB.",
        }, 413

    return app
