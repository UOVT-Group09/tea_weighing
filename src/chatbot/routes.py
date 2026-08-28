"""Chatbot HTTP endpoint.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

One JSON route, protected by the same session login as every other page.
The conversation history lives in the browser (sent with each request), so
the server stays stateless — same philosophy as db.py's open→run→close.
"""

import logging

from flask import Blueprint, jsonify, request

from ..auth import login_required
from . import llm

log = logging.getLogger(__name__)

bp = Blueprint("chatbot", __name__)

MAX_MESSAGE_LENGTH = 500
MAX_HISTORY_TURNS = 10


@bp.route("/api", methods=["POST"])
@login_required
def api():
    """Accept {message, history?} and return {reply}."""
    data = request.get_json(silent=True) or {}
    message = str(data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Please type a message."}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": "Message too long (max 500 characters)."}), 400

    history = data.get("history")
    if not isinstance(history, list):
        history = []

    try:
        reply = llm.chat(message, history[-MAX_HISTORY_TURNS:])
    except Exception:  # last-resort guard: never leak a stack trace (§5.5)
        log.exception("Chatbot failed to answer")
        reply = "Sorry, something went wrong. Please try again."

    return jsonify({"reply": reply})
