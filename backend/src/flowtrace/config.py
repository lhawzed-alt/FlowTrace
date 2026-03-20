import logging
import os
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None

load_dotenv()

ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw:
        try:
            return int(raw)
        except ValueError as exc:
            raise RuntimeError(f"Environment variable {name} must be an integer: {exc}") from exc
    return default


DB_CONFIG = {
    "host": _require_env("FLOWTRACE_DB_HOST"),
    "user": _require_env("FLOWTRACE_DB_USER"),
    "password": _require_env("FLOWTRACE_DB_PASSWORD"),
    "database": _require_env("FLOWTRACE_DB_NAME"),
    "port": _int_env("FLOWTRACE_DB_PORT", 3306),
    "charset": "utf8mb4",
    "connect_timeout": _int_env("FLOWTRACE_DB_CONNECT_TIMEOUT", 5),
}
TARGET_BASE_URL = _require_env("FLOWTRACE_TARGET_BASE_URL")
REPLAY_TIMEOUT = float(os.getenv("FLOWTRACE_REPLAY_TIMEOUT", "10"))
ALLOWED_REPLAY_HOSTS = set()
DB_POOL_MIN_CACHED = int(os.getenv("FLOWTRACE_DB_POOL_MIN_CACHED", "1"))
DB_POOL_MAX_CACHED = int(os.getenv("FLOWTRACE_DB_POOL_MAX_CACHED", "10"))


def _hosts_from_env(value: str | None) -> set[str]:
    if not value:
        return set()
    result = set()
    for chunk in value.split(","):
        chunk = chunk.strip()
        if chunk:
            result.add(chunk.lower())
    return result


def _hosts_from_url(url: str | None) -> set[str]:
    if not url:
        return set()
    parsed = urlparse(url)
    result = set()
    if parsed.hostname:
        hostname = parsed.hostname.lower()
        result.add(hostname)
        if parsed.port:
            result.add(f"{hostname}:{parsed.port}")
    if parsed.netloc:
        result.add(parsed.netloc.lower())
    return result


ALLOWED_REPLAY_HOSTS.update(_hosts_from_env(os.getenv("FLOWTRACE_REPLAY_ALLOWED_HOSTS")))
ALLOWED_REPLAY_HOSTS.update(_hosts_from_url(TARGET_BASE_URL))
if not ALLOWED_REPLAY_HOSTS:
    raise ValueError("Unable to build replay allow list because no hosts are configured")

FLOWTRACE_DEBUG = os.getenv("FLOWTRACE_DEBUG", "0").lower() in {"1", "true", "yes", "on"}
LOG_LEVEL = os.getenv("FLOWTRACE_LOG_LEVEL", "INFO").upper()
PORT = int(os.getenv("FLOWTRACE_PORT", "5000"))
PROJECT_NAME = "FlowTrace"
PROJECT_VERSION = os.getenv("FLOWTRACE_VERSION", "1.0.0")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("flowtrace")
