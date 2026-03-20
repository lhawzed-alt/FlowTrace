import logging
import os

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
