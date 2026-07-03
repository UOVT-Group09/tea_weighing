"""Seed a handful of demo farmers.

Standalone helper — not imported by the app. Farmer registration (add/edit)
is owned by D.M.N.D. Dissanayaka and still a stub, so this script is just a
stand-in to unblock manual testing of Weight Entry until that UI exists.

Run from the tea_weighing/ directory:
    python -m data.seed
"""

from src.app import create_app
from src.db import query, execute

SAMPLE_FARMERS = [
    ("R. Perera", "077 123 4567"),
    ("S. Kumari", "071 998 2210"),
    ("M. Bandara", "076 540 1199"),
    ("T. Fernando", "070 221 8830"),
]


def seed():
    app = create_app()
    with app.app_context():
        existing = query("SELECT COUNT(*) AS n FROM farmer", one=True)
        if existing and existing["n"] > 0:
            print(f"farmer table already has {existing['n']} row(s) — skipping seed.")
            return

        for name, contact in SAMPLE_FARMERS:
            execute("INSERT INTO farmer (name, contact) VALUES (%s, %s)", (name, contact))
        print(f"Seeded {len(SAMPLE_FARMERS)} sample farmers.")


if __name__ == "__main__":
    seed()
