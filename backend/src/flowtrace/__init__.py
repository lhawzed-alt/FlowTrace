from .config import logger


def create_app():
    from flask import Flask
    from flask_cors import CORS
    from .db import ensure_db_schema

    from .routes import register_routes

    app = Flask(__name__)
    CORS(app)
    register_routes(app)
    ensure_db_schema()
    logger.info("FlowTrace app created")
    return app
