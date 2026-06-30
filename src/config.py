"""Environment configuration.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

Centralises every environment-driven setting so the rest of the codebase never
reads ``os.environ`` directly. Values come from the process environment, which
is loaded from a local ``.env`` file in development (see ``.env.example``) and
from the platform dashboard in the cloud (Render/Railway).
"""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv

# Load .env once, at import time. In production the file is absent and the real
# environment variables are used instead — load_dotenv simply does nothing.
load_dotenv()


def _db_from_url(url):
    """Translate a single DATABASE_URL into individual connection parts.

    Cloud hosts often expose one URL such as
    ``mysql://user:pass@host:3306/dbname`` instead of separate variables.
    """
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "database": (parsed.path or "/").lstrip("/") or "tea_weighing",
    }


class Config:
    """Application-wide settings, read once from the environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = FLASK_ENV == "development"

    # Default operator seeded on first run when no operators exist.
    DEFAULT_OPERATOR_USERNAME = os.environ.get("DEFAULT_OPERATOR_USERNAME", "admin")
    DEFAULT_OPERATOR_PASSWORD = os.environ.get("DEFAULT_OPERATOR_PASSWORD", "admin123")

    # Database settings: prefer a single DATABASE_URL if the host provides one,
    # otherwise fall back to the discrete DB_* variables.
    _database_url = os.environ.get("DATABASE_URL")
    if _database_url:
        _db = _db_from_url(_database_url)
    else:
        _db = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", "3306")),
            "user": os.environ.get("DB_USER", "root"),
            "password": os.environ.get("DB_PASSWORD", ""),
            "database": os.environ.get("DB_NAME", "tea_weighing"),
        }

    DB_CONFIG = _db

    @classmethod
    def db_config(cls):
        """Return a copy of the MySQL connection keyword arguments."""
        return dict(cls.DB_CONFIG)
