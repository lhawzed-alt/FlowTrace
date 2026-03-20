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

DB_CONFIG = {
    "host": os.getenv("FLOWTRACE_DB_HOST", "localhost"),
    "user": os.getenv("FLOWTRACE_DB_USER", "root"),
    "password": os.getenv("FLOWTRACE_DB_PASSWORD", "0000"),
    "database": os.getenv("FLOWTRACE_DB_NAME", "flowtrace"),
    "port": int(os.getenv("FLOWTRACE_DB_PORT", "3306")),
    "charset": "utf8mb4",
    "connect_timeout": int(os.getenv("FLOWTRACE_DB_CONNECT_TIMEOUT", "5")),
}
TARGET_BASE_URL = os.getenv("FLOWTRACE_TARGET_BASE_URL", "http://localhost:5000")
REPLAY_TIMEOUT = float(os.getenv("FLOWTRACE_REPLAY_TIMEOUT", "10"))
ALLOWED_REPLAY_HOSTS = set()


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
