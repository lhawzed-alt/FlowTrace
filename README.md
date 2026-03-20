# FlowTrace

FlowTrace is a lightweight API request tracer + replay assistant. It records HTTP calls, exposes the latest history, and lets you reissue a saved request for testing/debugging purposes.

## Backend (Flask)

FlowTrace backend is packaged under `backend/src/flowtrace`, which exposes an application factory (`create_app`) plus helper modules for config, validation, replay orchestration, and database access. `backend/app.py` builds the Flask app and `backend/__main__.py` re-exports the same entrypoint so you can run the server with `python -m backend`.

### Requirements
1. Python 3.12+ (the project declares `requires-python = ">=3.12"`).
2. A MySQL-compatible database named `flowtrace` (credentials are configurable via `backend/.env.example` or your shell).
3. The dependencies defined in `backend/pyproject.toml` (install via `python -m pip install -e backend` to get an editable install plus CLI helpers).

### Env configuration
Create a `.env` file at the repository root (or set the vars in your shell) that mirrors `backend/.env.example`. Important variables:

- `FLOWTRACE_DB_HOST`, `FLOWTRACE_DB_PORT`, `FLOWTRACE_DB_USER`, `FLOWTRACE_DB_PASSWORD`, `FLOWTRACE_DB_NAME`: connection info for your database.
- `FLOWTRACE_PORT`: port the Flask app listens on (default `5000`).
- `FLOWTRACE_TARGET_BASE_URL`: base URL used for replaying relative request targets (defaults to `http://localhost:5000`).
- `FLOWTRACE_REPLAY_TIMEOUT`, `FLOWTRACE_DEBUG`, `FLOWTRACE_LOG_LEVEL`: control the downstream request timeout, debug mode, and log verbosity.

`.env` is already ignored by Git to keep secrets private.

### Running
```bash
python -m pip install -e backend
python -m backend
```

`FlowTrace` auto-creates the `api_requests` table (via `ensure_db_schema`) on startup, so you only need to ensure the database exists and credentials are valid.

### Testing
```bash
python -m unittest backend.tests.test_validation
```

### Key endpoints
- `POST /api/request`: persist a new request (validates `method`, `url`, and `status_code`).
- `GET /api/requests`: stream stored requests (latest first).
- `POST /api/replay/<id>`: replay a saved request while parsing JSON payloads.
- `GET /health`: a lightweight health check used by monitoring.

Helpful test routes remain available under `/api/test` and `/api/users` for frontend verification.

## Frontend

The UI is still a single static `frontend/index.html` file. Serve it via `python -m http.server 8000` from the `frontend/` directory or open it directly in the browser; it uses unpkg's `fetch` to talk to `http://127.0.0.1:5000` by default—adjust those URLs when pointing to another backend host/port.

## Work Done

1. Reorganized the backend into a package with dedicated modules (`config`, `db`, `validation`, `replay`, and `routes`) so future features can be plugged in cleanly.
2. Added an editable install entrypoint (`backend/app.py` + `backend/__main__.py`) plus structured logging/config via `python-dotenv`.
3. Introduced a small unit test covering validation logic and documented how to run it.
4. Expanded the README + `.env.example` documentation so new contributors understand the engineering workflow for both backend and frontend.
