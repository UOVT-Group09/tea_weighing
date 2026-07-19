"""Chatbot, RAG and data-tool tests.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

The LLM API is never called from tests: with no GROQ_API_KEY configured the
chatbot answers in offline "manual mode", which is exactly what we assert.
Database-backed tools are tested with the query helper monkeypatched, so the
suite passes with or without MySQL running.
"""

import pytest

from src.chatbot import llm, rag, tools
from src.db import DatabaseError
from tests.conftest import login


# ---------------------------------------------------------------------------
# RAG retrieval
# ---------------------------------------------------------------------------

def test_knowledge_base_loads_chunks():
    chunks = rag.load_chunks()
    assert len(chunks) >= 10  # several sections per markdown file
    assert all({"source", "heading", "text"} <= set(c) for c in chunks)


def test_retrieve_finds_error_check_section():
    results = rag.retrieve("why was a weight entry flagged", k=3)
    assert results, "expected at least one match"
    top_text = " ".join(r["heading"] + " " + r["text"] for r in results).lower()
    assert "flag" in top_text


def test_retrieve_finds_payment_formula():
    results = rag.retrieve("how is the farmer payment calculated", k=3)
    assert results
    assert any("payment" in r["text"].lower() for r in results)


def test_retrieve_returns_nothing_for_gibberish():
    assert rag.retrieve("qwertyzxcv nonexistentword", k=3) == []


# ---------------------------------------------------------------------------
# Data tools
# ---------------------------------------------------------------------------

def test_run_tool_rejects_unknown_name():
    result = tools.run_tool("drop_all_tables", {})
    assert "error" in result


def test_tools_survive_database_outage(monkeypatch):
    def boom(*args, **kwargs):
        raise DatabaseError("A database read error occurred.")

    monkeypatch.setattr(tools, "query", boom)
    for fn in (tools.list_farmers, tools.get_payment_summary, tools.get_tea_price):
        assert "error" in fn()
    assert "error" in tools.get_daily_summary("2026-01-01")


def test_search_app_knowledge_tool():
    result = tools.search_app_knowledge("trend estimate moving average")
    assert result["results"], "manual search should find the trend section"


# ---------------------------------------------------------------------------
# LLM fallback (no API key -> manual mode, no network access)
# ---------------------------------------------------------------------------

def test_chat_falls_back_without_api_key(monkeypatch):
    monkeypatch.setattr(llm.Config, "GROQ_API_KEY", "")
    reply = llm.chat("how do I change the tea price per kg?")
    assert "manual" in reply.lower()
    assert "price" in reply.lower()


# ---------------------------------------------------------------------------
# HTTP endpoint
# ---------------------------------------------------------------------------

def test_chat_endpoint_requires_login(client):
    response = client.post("/chatbot/api", json={"message": "hello"})
    assert response.status_code == 302  # redirected to the login page


def test_chat_endpoint_rejects_empty_message(client):
    login(client)
    response = client.post("/chatbot/api", json={"message": "   "})
    assert response.status_code == 400


def test_chat_endpoint_rejects_long_message(client):
    login(client)
    response = client.post("/chatbot/api", json={"message": "x" * 501})
    assert response.status_code == 400


def test_chat_endpoint_answers_in_manual_mode(client, monkeypatch):
    monkeypatch.setattr(llm.Config, "GROQ_API_KEY", "")
    login(client)
    response = client.post(
        "/chatbot/api",
        json={"message": "why was a weight flagged?", "history": []},
    )
    assert response.status_code == 200
    assert "flag" in response.get_json()["reply"].lower()
