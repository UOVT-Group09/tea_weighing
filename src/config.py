"""Environment configuration — the simple version.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

Reads settings from the environment. In development the values come from the
``.env`` file (copy ``.env.example`` to ``.env``); in the cloud they are set in
the host's dashboard. Nothing else happens here.
"""

import os

from dotenv import load_dotenv

# Load .env once. In production the file doesn't exist and this does nothing.
load_dotenv()


class Config:
    """Application-wide settings, read once from the environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = FLASK_ENV == "development"

    # Default operator seeded on first run when no operators exist.
    DEFAULT_OPERATOR_USERNAME = os.environ.get("DEFAULT_OPERATOR_USERNAME", "admin")
    DEFAULT_OPERATOR_PASSWORD = os.environ.get("DEFAULT_OPERATOR_PASSWORD", "admin123")

    # Chatbot (free Groq API tier). Leave GROQ_API_KEY empty to run the
    # chatbot in offline "manual mode" (answers from the built-in manual).
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    CHATBOT_MODEL = os.environ.get("CHATBOT_MODEL", "llama-3.3-70b-versatile")

    # MySQL connection settings, passed straight to mysql.connector.connect().
    DB_CONFIG = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "tea_weighing"),
    }
