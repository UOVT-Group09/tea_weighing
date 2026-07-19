"""LLM client for the chatbot — Groq free tier, with an offline fallback.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

Flow for every user message:

    1. rag.retrieve() pulls the most relevant manual sections (RAG).
    2. They are injected into the system prompt together with the rules.
    3. The conversation is sent to Groq's OpenAI-compatible chat endpoint.
    4. If the model asks for a tool (function calling), we run it via
       tools.run_tool() and send the result back — up to MAX_TOOL_ROUNDS.
    5. The final text reply is returned to the route.

If no GROQ_API_KEY is configured (or the API call fails) the chatbot drops
to "manual mode": it answers with the retrieved manual sections directly, so
the feature still demos without internet or an account.
"""

import json
import logging

import requests

from ..config import Config
from . import rag, tools

log = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TOOL_ROUNDS = 4
REQUEST_TIMEOUT = 30  # seconds

SYSTEM_PROMPT = """\
You are the built-in assistant of the Tea Leaves Weighing & Smart Records
System, a Flask web app used by tea collection centre operators in Sri Lanka.

Rules:
- Only answer questions about this system, its data, and tea collection work.
  Politely refuse anything else.
- For questions about live data (farmers, weights, payments, attendance,
  prices, flagged records) call the matching tool instead of guessing.
- For questions about how the app works, rely on the MANUAL EXCERPTS below.
- Be concise and friendly. The operators are non-technical.
- Currency is Sri Lankan Rupees (LKR); dates are YYYY-MM-DD.
- If a tool returns an "error" field, tell the user the database seems to be
  offline and suggest checking the dashboard banner.

MANUAL EXCERPTS (retrieved for this question):
{context}
"""


def _build_context(user_message):
    """Retrieve manual chunks and format them for the system prompt."""
    chunks = rag.retrieve(user_message, k=3)
    if not chunks:
        return "(nothing relevant found)", chunks
    text = "\n\n".join(
        f"[{c['source']} - {c['heading']}]\n{c['text']}" for c in chunks
    )
    return text, chunks


def _fallback_reply(user_message):
    """Manual-mode answer used when the LLM is not configured or fails."""
    chunks = rag.retrieve(user_message, k=2)
    if not chunks:
        return (
            "The AI model is not configured (no GROQ_API_KEY) and I couldn't "
            "find anything about that in the built-in manual. Try asking "
            "about farmers, weights, payments, attendance or reports."
        )
    # A chunk's text starts with its own heading line — drop it so the
    # heading isn't shown twice.
    sections = "\n\n".join(
        f"**{c['heading']}**\n{c['text'].partition(chr(10))[2].strip() or c['text']}"
        for c in chunks
    )
    return (
        "The AI model is offline, so here is the closest match from the "
        "built-in manual:\n\n" + sections
    )


def chat(user_message, history=None):
    """Answer one user message. Returns the reply text (never raises)."""
    if not Config.GROQ_API_KEY:
        return _fallback_reply(user_message)

    context, _ = _build_context(user_message)
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
    for turn in (history or [])[-10:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": str(turn["content"])[:2000]})
    messages.append({"role": "user", "content": user_message})

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            response = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {Config.GROQ_API_KEY}"},
                json={
                    "model": Config.CHATBOT_MODEL,
                    "messages": messages,
                    "tools": tools.openai_tool_specs(),
                    "temperature": 0.3,
                    "max_tokens": 800,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                return message.get("content") or "(no reply)"

            # The model asked for data — run each tool and hand back results.
            messages.append(message)
            for call in tool_calls:
                name = call["function"]["name"]
                try:
                    arguments = json.loads(call["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                log.info("Chatbot tool call: %s(%s)", name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": tools.run_tool(name, arguments),
                    }
                )

        return "Sorry — that question needed too many data lookups. Please try a simpler question."
    except requests.RequestException as exc:
        log.error("Groq API call failed: %s", exc)
        return _fallback_reply(user_message)
    except (KeyError, ValueError) as exc:
        log.error("Unexpected Groq API response: %s", exc)
        return _fallback_reply(user_message)
