"""Daily weight entry + smart error/anomaly check wiring.

Owner: K.G.C. Ravishan (Lead Dev — Weights & Smart Checks).

INTEGRATION STUB created by H.G.P.C. Sagara. Replace with the real weight-entry
flow: record a weight against the correct farmer, call checks.check() before
saving (guideline §5.2), and show the warning on screen.
"""

from flask import Blueprint, render_template

from .auth import login_required

bp = Blueprint("weights", __name__)


@bp.route("/")
@login_required
def index():
    return render_template(
        "_placeholder.html",
        module="Weight Entry",
        owner="K.G.C. Ravishan",
        todo="Daily weight entry linked to farmer + auto error/anomaly check (checks.py).",
    )
