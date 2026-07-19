"""In-app assistant: chatbot + RAG + shared data tools.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

The package is split the same way the rest of the system is — one concern per
module, all plain Python except the thin Flask layer:

    routes.py   Flask blueprint (``bp``) — the /chatbot/api endpoint
    rag.py      BM25 retrieval over the markdown knowledge base
    tools.py    read-only data tools (shared with the MCP server)
    llm.py      Groq chat completion + tool-calling loop, offline fallback
    knowledge/  markdown files the RAG index is built from

The same ``tools.py`` functions are exposed to external MCP clients (for
example Claude Desktop) by ``src/mcp_server.py`` — tools are defined once and
served two ways.
"""

from .routes import bp

__all__ = ["bp"]
