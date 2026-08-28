"""WSGI entry point for production servers.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

Vercel's Python runtime detects this file and serves the `app` object
below as a Vercel Function — see docs/deploy_vercel_tidb.md.
"""

from src.app import app

if __name__ == "__main__":
    app.run()
