from contextlib import closing
from datetime import datetime
from urllib.parse import urljoin
import json
import logging
import os

import pymysql
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}

DB_CONFIG = {
    "host": os.getenv("FLOWTRACE_DB_HOST", "localhost"),
    "user": os.getenv("FLOWTRACE_DB_USER", "root"),
    "password": os.getenv("FLOWTRACE_DB_PASSWORD", "0000"),
    "database": os.getenv("FLOWTRACE_DB_NAME", "flowtrace"),
    "port": int(os.getenv("FLOWTRACE_DB_PORT", "3306")),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": int(os.getenv("FLOWTRACE_DB_CONNECT_TIMEOUT", "5")),
}
TARGET_BASE_URL = os.getenv("FLOWTRACE_TARGET_BASE_URL", "http://localhost:5000")
REPLAY_TIMEOUT = float(os.getenv("FLOWTRACE_REPLAY_TIMEOUT", "10"))
FLOWTRACE_DEBUG = os.getenv("FLOWTRACE_DEBUG", "0").lower() in {"1", "true", "yes", "on"}
LOG_LEVEL = os.getenv("FLOWTRACE_LOG_LEVEL", "INFO").upper()
PORT = int(os.getenv("FLOWTRACE_PORT", "5000"))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("flowtrace")

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def ensure_db_schema():
    try:
        with closing(get_db_connection()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS api_requests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        method VARCHAR(10) NOT NULL,
                        url VARCHAR(500) NOT NULL,
                        status_code INT NOT NULL,
                        request_body TEXT,
                        response_body TEXT,
                        tags VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            connection.commit()
        logger.info("Table 'api_requests' exists or was created successfully")
    except pymysql.Error:
        logger.exception("Unable to ensure api_requests table exists")
        raise


@app.before_request
def initialize_schema():
    if getattr(app, "_schema_initialized", False):
        return
    ensure_db_schema()
    app._schema_initialized = True


def validate_api_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("JSON body is required")

    method = payload.get("method")
    if not method or not isinstance(method, str):
        raise ValueError("Field 'method' is required and has to be a string")
    method = method.upper()
    if method not in ALLOWED_METHODS:
        raise ValueError(f"Unsupported HTTP method '{method}'")

    url = payload.get("url")
    if not url or not isinstance(url, str):
        raise ValueError("Field 'url' is required and must be a string")
    url = url.strip()

    status_code = payload.get("status_code")
    if status_code is None:
        raise ValueError("Field 'status_code' is required")
    try:
        status_code = int(status_code)
    except (TypeError, ValueError):
        raise ValueError("Field 'status_code' must be an integer")
    if not 100 <= status_code <= 599:
        raise ValueError("Field 'status_code' must be between 100 and 599")

    request_body = payload.get("request_body") or ""
    response_body = payload.get("response_body") or ""
    tags = payload.get("tags") or ""

    return method, url, status_code, request_body, response_body, tags


def build_full_url(target_url):
    if target_url.lower().startswith(("http://", "https://")):
        return target_url
    base = TARGET_BASE_URL.rstrip("/") + "/"
    return urljoin(base, target_url.lstrip("/"))


def prepare_replay_payload(method, request_body):
    headers = {"Accept": "application/json"}
    params = None
    json_payload = None
    data_payload = None

    if not request_body:
        return headers, params, json_payload, data_payload

    try:
        parsed = json.loads(request_body)
    except json.JSONDecodeError:
        data_payload = request_body
        headers["Content-Type"] = "text/plain"
        return headers, params, json_payload, data_payload

    if method == "GET":
        params = parsed if isinstance(parsed, dict) else None
    else:
        json_payload = parsed

    return headers, params, json_payload, data_payload


def dispatch_replay(method, url, request_body):
    full_url = build_full_url(url)
    headers, params, json_payload, data_payload = prepare_replay_payload(method, request_body)

    response = requests.request(
        method,
        full_url,
        params=params,
        json=json_payload,
        data=data_payload,
        headers=headers,
        timeout=REPLAY_TIMEOUT,
    )
    if not response.ok:
        logger.warning("Replay request returned %s for %s %s", response.status_code, method, full_url)
    return response


@app.route("/api/request", methods=["POST"])
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
    except pymysql.Error:
        logger.exception("Database error while saving request")
        return jsonify({"error": "Database error"}), 500


@app.route("/api/requests", methods=["GET"])
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
    except pymysql.Error:
        logger.exception("Database error while querying requests")
        return jsonify({"error": "Database error"}), 500


@app.route("/api/replay/<int:request_id>", methods=["POST"])
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
    except pymysql.Error:
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
    except requests.RequestException as exc:
        logger.exception("Replay request failed for %s %s", method, url)
        return jsonify({"error": f"Request failed: {exc}"}), 502


@app.route("/api/test", methods=["GET"])
def test_get_endpoint():
    return jsonify({"message": "GET request successful", "timestamp": datetime.now().isoformat()}), 200


@app.route("/api/test", methods=["POST"])
def test_post_endpoint():
    payload = request.get_json(force=False, silent=True)
    return jsonify(
        {
            "message": "POST request successful",
            "received_data": payload,
            "timestamp": datetime.now().isoformat(),
        }
    ), 201


@app.route("/api/users", methods=["GET"])
def get_users():
    return jsonify(
        {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
            ],
            "count": 3,
            "timestamp": datetime.now().isoformat(),
        }
    ), 200


@app.route("/api/users", methods=["POST"])
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
                "timestamp": datetime.now().isoformat(),
            }
        ),
        201,
    )


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception("Unhandled exception")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    ensure_db_schema()
    logger.info("Starting Flask server on http://0.0.0.0:%s", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=FLOWTRACE_DEBUG)
