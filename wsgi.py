"""WSGI entry point for production servers.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

The cloud host (Render/Railway) starts the app with gunicorn:
    gunicorn wsgi:app
"""

from src.app import app

if __name__ == "__main__":
    app.run()
