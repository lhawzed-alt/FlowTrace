from .config import PROJECT_NAME, PROJECT_VERSION, logger
from .websocket import sock


def create_app():
    from flask import Flask
    from flask_cors import CORS
    from .db import ensure_db_schema

    from .routes import register_routes

    app = Flask(__name__)
    CORS(app)
    sock.init_app(app)
    register_routes(app)
    ensure_db_schema()

    @app.route("/", methods=["GET"])
    def root():
        from flask import jsonify

        return jsonify(
            {
                "service": PROJECT_NAME,
                "version": PROJECT_VERSION,
                "status": "healthy",
                "endpoints": [
                    {"path": "/api/request", "method": "POST"},
                    {"path": "/api/requests", "method": "GET"},
                    {"path": "/api/replay/<id>", "method": "POST"},
                    {"path": "/api/test", "method": "GET/POST"},
                    {"path": "/api/users", "method": "GET/POST"},
                    {"path": "/health", "method": "GET"},
                ],
            }
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        from flask import jsonify

        logger.debug("404 Not Found: %s %s", error.name, getattr(error, "description", ""))
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": "The requested URL does not match any FlowTrace route.",
                    "root": "/",
                }
            ),
            404,
        )

    logger.info("FlowTrace app created")
    return app
