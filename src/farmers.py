"""Farmer registry — CRUD.

Owner: D.M.N.D. Dissanayaka (DB & Payments) / shared.

INTEGRATION STUB created by H.G.P.C. Sagara so the blueprint is wired into the
app from day one. Replace the placeholder route below with the real farmer
CRUD (list / add / edit / delete) using the parameterised helpers in db.py.
"""

from flask import Blueprint, render_template

from .auth import login_required

bp = Blueprint("farmers", __name__)


@bp.route("/")
@login_required
def index():
    return render_template(
        "_placeholder.html",
        module="Farmers",
        owner="D.M.N.D. Dissanayaka",
        todo="Farmer CRUD: list, add, edit, delete (parameterised via db.execute/db.query).",
    )
