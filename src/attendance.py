"""Plucker attendance marking.

Owner: D.M.N.K. Disanayaka (QA, Testing & Attendance).

INTEGRATION STUB created by H.G.P.C. Sagara. Replace with attendance marking
(present/absent per plucker per day) feeding the wage calculation in payments.py.
"""

from flask import Blueprint, render_template

from .auth import login_required

bp = Blueprint("attendance", __name__)


@bp.route("/")
@login_required
def index():
    return render_template(
        "_placeholder.html",
        module="Attendance",
        owner="D.M.N.K. Disanayaka",
        todo="Mark plucker attendance per day; feeds plucker wage in payments.py.",
    )
