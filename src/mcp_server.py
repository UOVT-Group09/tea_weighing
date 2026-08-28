"""MCP server — exposes the system's data tools to any MCP client.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

MCP (Model Context Protocol) is an open standard that lets AI applications
such as Claude Desktop call tools in external systems. This server wraps the
exact same read-only functions the in-app chatbot uses (src/chatbot/tools.py)
and serves them over stdio — define once, expose twice.

Run manually (from the tea_weighing directory):

    .venv\\Scripts\\python.exe -m src.mcp_server

Normally you don't run it yourself — the MCP client (e.g. Claude Desktop)
launches it on demand. See docs/chatbot_rag_mcp_guide.md for the client
configuration.

Requires the ``mcp`` package (see requirements-mcp.txt). It is imported only
here, so the web app never needs it.
"""

from mcp.server.fastmcp import FastMCP

from .chatbot import tools

mcp = FastMCP("tea-weighing")


@mcp.tool()
def list_farmers() -> dict:
    """List every registered farmer with id, name and contact."""
    return tools.list_farmers()


@mcp.tool()
def get_farmer_summary(farmer_name: str) -> dict:
    """Totals, recent weights and supply trend for one farmer, matched by
    full or partial name."""
    return tools.get_farmer_summary(farmer_name)


@mcp.tool()
def get_daily_summary(date: str = "") -> dict:
    """Collection summary (total kg, entries, flagged count, farmers) for a
    date in YYYY-MM-DD format. Empty string means today."""
    return tools.get_daily_summary(date or None)


@mcp.tool()
def get_flagged_records(limit: int = 10) -> dict:
    """Most recent weight entries flagged by the automatic error check."""
    return tools.get_flagged_records(limit)


@mcp.tool()
def get_payment_summary() -> dict:
    """Per-farmer payable amounts (unflagged kg x current price) and
    per-plucker wages."""
    return tools.get_payment_summary()


@mcp.tool()
def get_attendance_summary(date: str = "") -> dict:
    """Plucker attendance for a date in YYYY-MM-DD format. Empty string
    means today."""
    return tools.get_attendance_summary(date or None)


@mcp.tool()
def get_tea_price() -> dict:
    """The tea price per kg currently used for payments (LKR)."""
    return tools.get_tea_price()


@mcp.tool()
def search_app_knowledge(question: str) -> dict:
    """Search the system's built-in user manual (how features and formulas
    work) and return the most relevant sections."""
    return tools.search_app_knowledge(question)


if __name__ == "__main__":
    mcp.run()  # stdio transport — the client speaks to us over stdin/stdout
