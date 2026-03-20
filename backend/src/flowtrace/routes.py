from contextlib import closing

from flask import Blueprint, jsonify, request

from .config import logger
from .db import get_db_connection
from .replay import dispatch_replay
from .validation import validate_api_payload


def register_routes(app):
    api = Blueprint("api", __name__)

    @api.route("/api/request", methods=["POST"])
    def save_api_request():
        payload = request.get_json()

        try:
            method, url, status_code, request_body, response_body, tags = validate_api_payload(payload)
        except ValueError as exc:
            logger.warning("Validation failed while saving API request: %s", exc)
            return jsonify({"error": str(exc)}), 400

        try:
            with closing(get_db_connection()) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO api_requests (method, url, status_code, request_body, response_body, tags)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (method, url, status_code, request_body, response_body, tags),
                    )
                connection.commit()
            return jsonify({"message": "saved"}), 201
        except Exception:
            logger.exception("Database error while saving request")
            return jsonify({"error": "Database error"}), 500

    @api.route("/api/requests", methods=["GET"])
    def get_api_requests():
        try:
            with closing(get_db_connection()) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, method, url, status_code, request_body, response_body, tags,
                               DATE_FORMAT(created_at, "%Y-%m-%d %H:%i:%s") as created_at
                        FROM api_requests
                        ORDER BY created_at DESC
                        """
                    )
                    results = cursor.fetchall()
            return jsonify(results), 200
        except Exception:
            logger.exception("Database error while querying requests")
            return jsonify({"error": "Database error"}), 500

    @api.route("/api/replay/<int:request_id>", methods=["POST"])
    def replay_api_request(request_id):
        try:
            with closing(get_db_connection()) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT method, url, request_body
                        FROM api_requests
                        WHERE id = %s
                        """,
                        (request_id,),
                    )
                    record = cursor.fetchone()
        except Exception:
            logger.exception("Database error while fetching request %s", request_id)
            return jsonify({"error": "Database error"}), 500

        if not record:
            return jsonify({"error": "Record not found"}), 404

        method = record["method"].upper()
        url = record["url"]
        request_body = record.get("request_body", "")

        try:
            response = dispatch_replay(method, url, request_body)
            return jsonify(
                {
                    "status_code": response.status_code,
                    "response_body": response.text,
                }
            ), 200
        except Exception as exc:
            logger.exception("Replay request failed for %s %s", method, url)
            return jsonify({"error": f"Request failed: {exc}"}), 502

    @api.route("/api/test", methods=["GET"])
    def test_get_endpoint():
        return jsonify({"message": "GET request successful"}), 200

    @api.route("/api/test", methods=["POST"])
    def test_post_endpoint():
        payload = request.get_json(force=False, silent=True)
        return jsonify(
            {
                "message": "POST request successful",
                "received_data": payload,
            }
        ), 201

    @api.route("/api/users", methods=["GET"])
    def get_users():
        return jsonify(
            {
                "users": [
                    {"id": 1, "name": "Alice", "email": "alice@example.com"},
                    {"id": 2, "name": "Bob", "email": "bob@example.com"},
                    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
                ],
                "count": 3,
            }
        ), 200

    @api.route("/api/users", methods=["POST"])
    def create_user():
        payload = request.get_json(force=False, silent=True) or {}
        name = payload.get("name")
        if not name:
            return jsonify({"error": "Name is required"}), 400

        new_user = {
            "id": 100,
            "name": name,
            "email": payload.get("email", f"{name.lower()}@example.com"),
        }
        return (
            jsonify(
                {
                    "message": "User created successfully",
                    "user": new_user,
                }
            ),
            201,
        )

    app.register_blueprint(api)

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "healthy"}), 200

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unhandled exception")
        return jsonify({"error": "Internal server error"}), 500
