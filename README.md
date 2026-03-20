# FlowTrace

FlowTrace is a lightweight API request tracer + replay assistant. It records HTTP calls, exposes the latest history, and lets you reissue a saved request for testing/debugging purposes.

## Backend (Flask)

### Requirements
1. Python 3.12+ (the project declares `requires-python = ">=3.12"`).
2. A MySQL-compatible database named `flowtrace` (credentials are configurable via env).
3. `python-dotenv`, `flask`, `flask-cors`, `pymysql`, and `requests` (the easiest way to install them is `python -m pip install -e backend`).

### Env configuration
Create a `.env` file at the repository root (or set the vars in your shell) that mirrors `backend/.env.example`. Important variables:

- `FLOWTRACE_DB_HOST`, `FLOWTRACE_DB_PORT`, `FLOWTRACE_DB_USER`, `FLOWTRACE_DB_PASSWORD`, `FLOWTRACE_DB_NAME`: connection info for your database.
- `FLOWTRACE_PORT`: port the Flask app listens on (default `5000`).
- `FLOWTRACE_TARGET_BASE_URL`: used during replay for relative URLs (defaults to `http://localhost:5000`).
- `FLOWTRACE_REPLAY_TIMEOUT`, `FLOWTRACE_DEBUG`, `FLOWTRACE_LOG_LEVEL`: control the replay timeout, debug mode, and log verbosity.

`.env` is already ignored by Git; keep secrets out of version control.

### Running
```bash
python -m pip install -e backend
python -m backend.app
```

The server creates the `api_requests` table automatically on first request, thanks to the schema guard in `app.py`.

### Key endpoints
- `POST /api/request`: persist a new request (validates `method`, `url`, and `status_code`).
- `GET /api/requests`: stream the stored requests (latest first).
- `POST /api/replay/<id>`: replays the saved request using the recorded body (JSON payloads are parsed and forwarded as JSON).
- `GET /health`: simple health check used by monitoring.

Helpful test routes are available under `/api/test` and `/api/users` for frontend verification.

## Frontend

The UI is a single static `frontend/index.html` file. You can open it directly in a browser or serve it via `python -m http.server 8000` from the `frontend/` directory to work around CORS restrictions.

By default it talks to `http://127.0.0.1:5000`; update the fetch URLs in `frontend/index.html` if you point the backend elsewhere.

## Work Done

1. Centralized configuration using `python-dotenv` + env variables, so credentials and replay targets are not hard-coded.
2. Added request payload validation plus structured logging to improve observability and prevent bad data from entering the database.
3. Hardened the replay endpoint by separating JSON/text handling, logging non-OK responses, and keeping the original response body even when downstream APIs return 4xx/5xx.
4. Recorded documentation and an `.env.example` to clarify setup for teammates.

Feel free to reach out if you'd like help wiring this into CI, adding automated tests, or polishing the frontend experience.
